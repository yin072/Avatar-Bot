import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_qdrant import Qdrant  # 使用新版Qdrant集成
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from Config import Config
import warnings


class QdrantLoader:
    def __init__(self):
        # 初始化嵌入模型（确保与Config中的模型名称一致）
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # 如果没有GPU则使用cpu
            encode_kwargs={'normalize_embeddings': False}
        )
        
        # 初始化Qdrant客户端
        self.collection_name = Config.QDRANT_COLLECTION
        self.qdrant_client = QdrantClient(
            path=Config.QDRANT_PATH,
            prefer_grpc=False  # Windows下建议关闭grpc
        )
        
        # 确保集合存在
        self._ensure_collection_exists()
        
        # 初始化LangChain Qdrant包装器
        self.client = Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )

    def _ensure_collection_exists(self):
        """确保Qdrant集合存在且配置正确"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            # 验证向量维度是否匹配（M3E模型通常是768维）
            if collection_info.config.params.vectors.size != 768:
                raise ValueError("Existing collection has wrong vector size")
        except Exception:
            # 集合不存在或配置错误，重新创建
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,  # M3E-base模型输出768维
                    distance=Distance.COSINE
                )
            )

    def load_txt_files(self, input_folder):
        """遍历文件夹，获取所有txt文件（优化版）"""
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(input_folder)
            for file in files
            if file.endswith('.txt')
        ]

    def chunk_text(self, text, chunk_size=300, chunk_overlap=50):
        """
        优化后的文本分块方法
        """
        
        """
        改进分块策略：首先，按行分割每一句对话，按照首先设定的分块大小填充对话，
        当满了之后检查有多少条对话，如果过少就说明有长对话。此时扩大块大小，
        如此循环，得出一个分块列表，在这个过程中确保单条对话不被分割，
        按照预先设定的上下文大小保留上下文（使用队列先保存上下文，在下一个块开始时把队列里的内容添加进去）
        """
        
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n",  # 按行分割更合理
            strip_whitespace=True
        )
        return text_splitter.split_text(text)

    def process_files(self, input_folder):
        """批量处理文件（带错误处理）"""
        txt_files = self.load_txt_files(input_folder)
        if not txt_files:
            print(f"警告：在 {input_folder} 中未找到任何聊天记录文件")
            return

        for file_path in txt_files:
            try:
                print(f"正在处理: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                chunks = self.chunk_text(content)
                if not chunks:
                    continue
                
                # 批量插入（优化性能）
                self.client.add_texts(
                    texts=chunks,
                    metadatas=[{
                        "source_file": os.path.basename(file_path),
                        "file_path": file_path
                    } for _ in chunks],
                    batch_size=100  # 分批插入防止内存不足
                )
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {str(e)}")
                continue