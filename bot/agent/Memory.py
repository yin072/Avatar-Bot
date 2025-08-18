from dotenv import load_dotenv
import os
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv("bot/config.env")

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
     
     #长时记忆实现   
    def get_memory_and_set_memory(self,MemoryId):
        "获取与用户对话的记忆"""
        
        """工作流程如下：
        1. **初始化时**，`self.memory` 为空，从 `get_memory()` 获取历史记录（若无则为空）。
        2. **`ConversationTokenBufferMemory`** 使用 `self.memory` 来存储对话历史。
        3. 每次对话后，`self.memory` 会更新，存储新的用户和 AI 消息。
        4. **超过 10 条消息时**，`get_memory()` 会生成摘要并清空历史记录，将摘要存回 Redis。
        5. **循环**：每次有新消息，`self.memory` 会更新，`get_memory()` 会重新生成并存储摘要，确保记忆管理。

        最终，`ConversationTokenBufferMemory` 管理内存，`RedisChatMessageHistory` 负责持久化存储。
        """
        chat_message_history = RedisChatMessageHistory(
            url=os.getenv("REDIS_URL"),session_id=MemoryId
        )
        store_message = chat_message_history.messages
        if len(store_message) > 10:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "这是一段你模仿了一个人的聊天数据和然后跟另一个微信用户的当前对话记忆，对其进行总结摘要，摘要使用第一人称‘我’，并且提取其中的当前微信用户关键信息，如姓名、年龄、性别、出生日期和刚刚述说的事情等。以如下格式返回:\n 总结摘要内容｜用户关键信息 \n 例如 用户张三问我在干嘛，我说没干嘛，然后他问我今天干啥了，我说在家待着没干嘛。｜张三,生日1999年1月1日"
                    ),
                    ("user","{input}"),
                ]
            )
            chain = prompt | self.chatmodel 
            summary = chain.invoke({"input":store_message})
            chat_message_history.clear()
            chat_message_history.add_message(summary)
        return chat_message_history
    