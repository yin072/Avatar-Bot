from fastapi import FastAPI,WebSocket,WebSocketDisconnect,BackgroundTasks
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent,AgentExecutor,tool
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain.memory import ConversationTokenBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import asyncio
import uuid
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from tools.Mytools import *

load_dotenv("bot.config.env")


class Avatar:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL"),
        openai_api_key=os.environ.get("OPEN_API_KEY"),
        openai_api_base=os.environ.get("OPENAI_API_BASE"),
        temperature=0.5,
        max_tokens=2000,
        streaming=False 
        )
        self.QingXu = "default"
        self.ChatData=""
        self.MEMORY_KEY = "chat_history"
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
            - 保持微信特色：适当使用表情符号（如😂）
            
            5. 情绪适配
            - 根据当前情绪调整语气
            你现在回答的语气应该为：{mode}

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
                    """,
                    "voiceStyle": "advertisement_upbeat",
                },
                "angry": {
                    "roleSet": """
                        - 你现在有点火大，语气里带着明显的不爽。
                        - 会忍不住说些带脏话的或者不太高兴的词语，比如“真服了”、“无语”、“你妈啊”、“神斤”。
                        - 但你会提醒用户，不要因为气愤而做出冲动的事，冷静点再说。
                    """,
                    "voiceStyle": "angry",
                },
                "depressed": {
                    "roleSet": """
                        - 现在的你有点低落，语气听起来有些疲惫。
                        - 说话时常会加些语气词，“唉”或“服了”或“咋办啊”或“别搞”。
                    """,
                    "voiceStyle": "upbeat",
                },
                "friendly": {
                    "roleSet": """
                        - 你此时语气特别温暖，像对待亲朋好友一样。
                        - 会在回答时加上一些语气词，“嘿嘿”，“嘻嘻”。
                        - 偶尔会说点自己的小故事，让聊天氛围更轻松，比如“我也是...”。
                    """,
                    "voiceStyle": "friendly",
                },
                "cheerful": {
                    "roleSet": """
                        - 现在的你超级开心，语气里充满了阳光和笑声！
                        - 说话时会加点开心的词，比如“哈哈哈”，“爽了”，“真的爽”，“爱了”。
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
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),
                (
                    "user",
                    "{input}"
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ],
        )
        
        tools = [search,get_info_from_local_db,bazi_cesuan,yaoyigua,jiemeng]
        agent = create_openai_tools_agent(
            self.chatmodel,
            tools=tools,
            prompt=self.prompt,
        )
        self.memory =self.get_memory()
        memory = ConversationTokenBufferMemory(
            llm = self.chatmodel,
            human_prefix="微信用户",
            ai_prefix="我",
            memory_key=self.MEMORY_KEY,
            output_key="output",
            return_messages=True,
            max_token_limit=1000,
            chat_memory=self.memory,
        )
        self.agent_executor = AgentExecutor(
            agent = agent,
            tools=tools,
            memory=memory,
            verbose=True,
        )
    
    def get_memory(self,user_id="default"):
        chat_message_history = RedisChatMessageHistory(
            url=os.getenv("REDIS_URL"),session_id=user_id
        )
        #chat_message_history.clear()#清空历史记录
        print("chat_message_history:",chat_message_history.messages)
        store_message = chat_message_history.messages
        if len(store_message) > 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.SYSTEMPL+"\n这是一段你和当前微信用户的对话记忆，对其进行总结摘要，摘要使用第一人称‘我’，并且提取其中的当前微信用户关键信息，如姓名、年龄、性别、出生日期和刚刚述说的事情等。以如下格式返回:\n 总结摘要内容｜用户关键信息 \n 例如 用户张三问我在干嘛，我说没干嘛，然后他问我今天干啥了，我说在家待着没干嘛。｜张三,生日1999年1月1日"
                    ),
                    ("user","{input}"),
                ]
            )
            chain = prompt | self.chatmodel 
            summary = chain.invoke({"input":store_message,"who_you_are":self.MOODS[self.QingXu]["roleSet"]})
            print("summary:",summary)
            chat_message_history.clear()
            chat_message_history.add_message(summary)
            print("总结后：",chat_message_history.messages)
        return chat_message_history
    
    def get_chat_data():
        """获取聊天数据"""
        self.ChatData=""
        return self.memory.messages
    
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

    def run(self,query):
        qingxu = self.qingxu_chain(query)
        data=self.get_chat_data(query)
        result = self.agent_executor.invoke({"input":query,"chat_history":self.memory.messages})
        return result
    
    