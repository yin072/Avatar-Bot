from dotenv import load_dotenv
import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_qdrant import Qdrant  # 使用新版Qdrant集成
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

from typing import List
from langchain_core.documents import Document

load_dotenv("bot.config.env")

class Memory:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL"),
        openai_api_key=os.environ.get("OPEN_API_KEY"),
        openai_api_base=os.environ.get("OPENAI_API_BASE"),
        temperature=0.5,
        max_tokens=2000,
        streaming=False 
        )
        
    def get_memory_and_set_memory(self,MemoryId):
        "获取与用户对话的短时记忆，并总结至长时记忆库"""
        chat_message_history = RedisChatMessageHistory(
            url=os.getenv("REDIS_URL"),session_id=MemoryId
        )
        print("chat_message_history:",chat_message_history.messages)
        store_message = chat_message_history.messages
        if len(store_message) > 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "这是一段你模仿聊天数据和当前微信用户的对话记忆，对其进行总结摘要，摘要使用第一人称‘我’，并且提取其中的当前微信用户关键信息，如姓名、年龄、性别、出生日期和刚刚述说的事情等。以如下格式返回:\n 总结摘要内容｜用户关键信息 \n 例如 用户张三问我在干嘛，我说没干嘛，然后他问我今天干啥了，我说在家待着没干嘛。｜张三,生日1999年1月1日"
                    ),
                    ("user","{input}"),
                ]
            )
            chain = prompt | self.chatmodel 
            summary = chain.invoke({"input":store_message})
            print("summary:",summary)
            # 调用qdrant存储方法
            self.qdrant_load(
                summary_content=str(summary),
                memory_id=MemoryId,
                metadata={
                    "source": "wechat",
                    "summary_type": "conversation"
                }
            )
            chat_message_history.clear()
            chat_message_history.add_message(summary)
            print("总结后：",chat_message_history.messages)
        return chat_message_history
    
    def get_new_long_memory(self,MemoryId):
        "获取新的与用户对话的长期记忆"""
        
        
    def qdrant_load(self, summary_content: str, memory_id: str, metadata: dict = None):
        """将总结的记忆存入本地Qdrant向量数据库
        
        Args:
            summary_content: 要存储的总结文本内容
            memory_id: 记忆的唯一标识符
            metadata: 额外的元数据 (默认为None)
        """
        # 初始化本地Qdrant客户端
        qdrant_client = QdrantClient(path="bot/local_qdrand")  # 指定本地存储路径
        
        # 初始化嵌入模型 (使用你已导入的HuggingFaceEmbeddings)
        embeddings = HuggingFaceEmbeddings(
            model_name="moka-ai/m3e-base",  # 推荐的中文嵌入模型
            model_kwargs={'device': 'cpu'}
        )
        
        # 创建LangChain的Qdrant实例
        qdrant = Qdrant(
            client=qdrant_client,
            collection_name="memory_summaries",  # 指定集合名称
            embeddings=embeddings
        )
        
        # 准备文档对象
        doc = Document(
            page_content=summary_content,
            metadata={
                "memory_id": memory_id,
                "type": "memory_summary",
                "timestamp": datetime.datetime.now().isoformat(),
                **(metadata or {})  # 合并额外元数据
            }
        )
        
        # 存入向量数据库
        qdrant.add_documents([doc])
        print(f"已成功将记忆 {memory_id} 存入Qdrant数据库")