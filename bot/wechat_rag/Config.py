import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("bot/config.env")

class Config:
    # Qdrant 配置
    QDRANT_PATH = os.getenv("QDRANT_PATH")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "wechat_chat_history")
    
    # 嵌入模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    
    # 微信数据路径配置
    DATA_DIR = os.getenv("DATA_DIR", "wxdump_work\export")
    PROCESSED_DIR = os.getenv("PROCESSED_DIR", "wxdump_work\export")
    