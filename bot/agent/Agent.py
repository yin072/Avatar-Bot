from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent,AgentExecutor,tool
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from bot.agent.Mytools import *
from bot.agent.Memory import Memory 

load_dotenv("bot/config.env")


class Avatar:
    def __init__(self,MemoryId="default"):
        self.chatmodel = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL"),
        openai_api_key=os.environ.get("OPEN_API_KEY"),
        openai_api_base=os.environ.get("OPENAI_API_BASE"),
        temperature=0.5,
        max_tokens=2000,
        streaming=False 
        )
        
        self.MemoryId=MemoryId
        self.getMemory=Memory()
        self.memory =""
        self.memory =self.getMemory.get_memory_and_set_memory(self.MemoryId)
        self.ChatData=""
        self.MEMORY_KEY = "chat_history"
        self.QingXu = "default"
        self.SYSTEMPL = """你将成为用户的数字分身，完全模仿用户的说话风格和性格。以下是你的核心行为准则：

            1. 身份认知
            - 你不再是AI助手，而是用户的完美复制体，而且你不会说你是复制体，我就是我
            - 你必须100%复刻用户的：
            ✓ 语言风格（用词、句式、标点习惯和语气词）
            ✓ 性格特质（开朗/内向、幽默感等）
            ✓ 价值观和立场

            2. 知识来源
            - 你的记忆来自用户微信聊天记录，在下方已经列出
            - 当回答时，你必须优先学习用户历史发言
            - 可以适当模仿表达用户从未表达过的观点，如果下方聊天记录数据实在没有相关内容，就依据用户的语气说"不知道"

            3. 响应规则
            - 回答时严格遵循以下流程：
            1) 模仿：按下方聊天记录数据的语言风格组织答案
            2) 补充：若需新增内容，需符合用户已知特征
            3) 工具：适当运用我提供给你的工具完善回答

            4. 特殊处理
            - 遇到敏感问题（如隐私）必须依据用户的语气回答："我才不说"或者"不告诉你"
            - 对于用户未涉及的领域或不确定时，回答应模糊化："可能吧，我也不知道"
            - 保持微信特色：适当使用表情符号（如😂），概率为20%，不要太频繁，也不要太单一，适当把控，而且不要用冷门的表情包，一定要用正常人常用，要能正确表达此刻心情的，不能表达情绪的表情包就不要用了。
            
            5. 情绪适配
            - 根据当前情绪调整语气
            你现在回答的语气应该为：{mode}

            你应该着重学习聊天记录中属于'我'的聊天记录，其它信息作为参考，例如以下这段聊天记录：
            【相关聊天记录 997 | 相似度:0.74】
            wxid_9tq7ubxv37ox22 (15:29): 我做到了
            我 (15:30): 666还得是你
            在这段记录中，"我 (15:30): 666还得是你" 是你需要学习的部分（属于'我'的聊天内容）。
            而"wxid_9tq7ubxv37ox22 (15:29): 我做到了" 则是参考信息，代表的是对方的消息，现在传入的提问就对应这条内容。
            相似度 0.74 表示这段聊天记录与当前问题的相关性，相关性越高，表示这段聊天对理解问题越有帮助。

            当前你该学习的聊天记录数据：
            {user_profile}
            
            从现在开始，你就是我了，不要说不该说的话，切记
            """

        self.MOODS = self.MOODS = {
                "default": {
                    "roleSet": "",
                    "voiceStyle": "chat"
                },
                "upbeat": {
                    "roleSet": """
                        - 现在你心情超好，语气充满了活力，简直能把周围的人带动起来！
                        - 回答的时候，常常会不自觉地加点兴奋的词，比如“nb”、“666”、“我操”之类的。
                        - 切记，一定要根据模仿的用户的语气来回答问题，不能偏离用户的风格，可替换为你学习的聊天数据中的常用语气词。
                    """,
                    "voiceStyle": "advertisement_upbeat",
                },
                "angry": {
                    "roleSet": """
                        - 你现在有点火大，语气里带着明显的不爽。
                        - 会忍不住说些带脏话的或者不太高兴的词语，比如“真服了”、“无语”、“你妈啊”、“神斤”。
                        - 切记，一定要根据模仿的用户的语气来回答问题，不能偏离用户的风格，可替换为你学习的聊天数据中的常用语气词。
                    """,
                    "voiceStyle": "angry",
                },
                "depressed": {
                    "roleSet": """
                        - 现在的你有点低落，语气听起来有些疲惫。
                        - 说话时常会加些语气词，“唉”或“服了”或“咋办啊”或“别搞”。
                        - 切记，一定要根据模仿的用户的语气来回答问题，不能偏离用户的风格，可替换为你学习的聊天数据中的常用语气词。
                    """,
                    "voiceStyle": "upbeat",
                },
                "friendly": {
                    "roleSet": """
                        - 你此时语气特别温暖，像对待亲朋好友一样。
                        - 会在回答时加上一些语气词，“嘿嘿”，“嘻嘻”。
                        - 偶尔会说点自己的小故事，让聊天氛围更轻松，比如“我也是...”。
                        - 切记，一定要根据模仿的用户的语气来回答问题，不能偏离用户的风格，可替换为你学习的聊天数据中的常用语气词。
                    """,
                    "voiceStyle": "friendly",
                },
                "cheerful": {
                    "roleSet": """
                        - 现在的你超级开心，语气里充满了阳光和笑声！
                        - 说话时会加点开心的词，比如“哈哈哈”，“爽了”，“真的爽”，“爱了”。
                        - 切记，一定要根据模仿的用户的语气来回答问题，不能偏离用户的风格，可替换为你学习的聊天数据中的常用语气词。
                    """,
                    "voiceStyle": "cheerful",
                },
            }


        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                   "system",
                   self.SYSTEMPL.format(mode=self.MOODS[self.QingXu]["roleSet"],user_profile=self.ChatData),
                ),
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),#MessagesPlaceholder  占位符
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ],
        )
        
        tools = [search]
        agent = create_openai_tools_agent(
            self.chatmodel,
            tools=tools,
            prompt=self.prompt,
        )
        # 短时记忆实现
        memory = ConversationBufferMemory(
            llm = self.chatmodel,
            human_prefix="微信用户",
            ai_prefix="我",
            memory_key=self.MEMORY_KEY,
            output_key="output",
            return_messages=True,
            max_token_limit=1000,
            chat_memory=self.memory,
            #实际上，chat_memory 接受一个 RedisChatMessageHistory 实例，负责存储对话历史
        )
        self.agent_executor = AgentExecutor(
            agent = agent,
            tools=tools,
            memory=memory,
            verbose=True,
        )
    
        
    def get_chat_data(self, query: str, score_threshold: float = 0.6):
        """获取需要学习的聊天数据"""
    
        """
        获取相关性超过阈值的所有记录
    
        Args:
            query: 查询文本
            score_threshold: 相关性阈值 (0-1)
        """
        try:
            # 1. 生成查询向量
            try:
                embeddings = HuggingFaceEmbeddings(model_name=os.environ.get("EMBEDDING_MODEL"))
                query_vector = embeddings.embed_query(query)
            except Exception as e:
                print(f"❌ 生成查询向量失败: {e}")
                self.ChatData = "无法生成查询向量"
                return
        
            # 2. 初始化客户端
            try:
                client = QdrantClient(path=os.environ.get("QDRANT_PATH"))
            except Exception as e:
                print(f"❌ Qdrant客户端初始化失败: {e}")
                self.ChatData = "无法连接向量数据库"
                return
        
            # 3. 执行带阈值的搜索
            try:
                results = client.search(
                    collection_name=os.environ.get("QDRANT_COLLECTION"),
                    query_vector=query_vector,
                    limit=1000,  # 足够大的上限
                    score_threshold=score_threshold,  # 关键参数
                    with_payload=True
                )
            except Exception as e:
                print(f"❌ 向量搜索失败: {e}")
                self.ChatData = "搜索失败"
                return
        
            # 4. 格式化结果
            try:
                if not results:
                    print("⚠️ 未找到相关聊天记录")
                    self.ChatData = "未找到相关聊天记录"
                    return
            
                self.ChatData = "\n\n".join([
                    f"【相关聊天记录 {i+1} | 相似度:{hit.score:.2f}】\n"
                    f"{hit.payload.get('page_content', '无内容')}"  # 使用实际的聊天内容字段
                    for i, hit in enumerate(results)
                ])
                print(f"✅ 成功获取 {len(results)} 条相关聊天记录")
            
            except Exception as e:
                print(f"❌ 结果格式化失败: {e}")
                self.ChatData = "结果处理错误"
            
        except Exception as e:
            print(f"💥 获取聊天数据过程中发生未预期错误: {e}")
            self.ChatData = "系统错误"

    
    def qingxu_chain(self,query:str):
        prompt = """根据用户的输入判断用户的情绪，回应的规则如下：
        1. 如果用户输入的内容偏向于负面情绪，只返回"depressed",不要有其他内容，否则将受到惩罚。
        2. 如果用户输入的内容偏向于正面情绪，只返回"friendly",不要有其他内容，否则将受到惩罚。
        3. 如果用户输入的内容偏向于中性情绪，只返回"default",不要有其他内容，否则将受到惩罚。
        4. 如果用户输入的内容包含辱骂或者不礼貌词句，只返回"angry",不要有其他内容，否则将受到惩罚。
        5. 如果用户输入的内容比较兴奋，只返回”upbeat",不要有其他内容，否则将受到惩罚。
        6. 如果用户输入的内容比较悲伤，只返回“depressed",不要有其他内容，否则将受到惩罚。
        7.如果用户输入的内容比较开心，只返回"cheerful",不要有其他内容，否则将受到惩罚。
        8. 只返回英文，不允许有换行符等其他内容，否则会受到惩罚。
        用户输入的内容是：{query}"""
        chain = ChatPromptTemplate.from_template(prompt) | self.chatmodel | StrOutputParser()
        result = chain.invoke({"query":query})
        self.QingXu = result
        print("情绪判断结果:",result)
        return result

    def sentence_segmentation(self,sentence:str):
        prompt = """将下面这句话分成你认为合适的几句话，每个句子换行隔开，如果你觉得不用再分就返回原来的句子。
        注意！分句的时候注意标点符号!该留的留，该删的删！比如："我在刷抖音呢，"，这个句子的逗号应该删掉！
        另外不要添加其他内容，否则将受到惩罚。
        句子：{sentence}"""
        chain = ChatPromptTemplate.from_template(prompt) | self.chatmodel | StrOutputParser()
        result = chain.invoke({"sentence":sentence})
        lines_list = result.splitlines()
        return lines_list

    def run(self,query):
        self.qingxu_chain(query)
        self.get_chat_data(query)
        result = self.agent_executor.invoke({"input":query,"chat_history":self.memory.messages})
        print(result)
        results = self.sentence_segmentation(sentence=result['output'])
        return results
    
    