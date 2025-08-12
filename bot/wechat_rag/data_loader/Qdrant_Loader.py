import os
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from transformers import AutoTokenizer, AutoModel
import torch
import uuid
from Config import Config
from langchain.text_splitter import CharacterTextSplitter

class QdrantLoader:
    def __init__(self):
        # 初始化Qdrant客户端
        self.client = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
        self.collection_name = Config.QDRANT_COLLECTION
        
        # 加载嵌入模型
        self.tokenizer = AutoTokenizer.from_pretrained(Config.EMBEDDING_MODEL)
        self.model = AutoModel.from_pretrained(Config.EMBEDDING_MODEL)

        # 创建 Qdrant collection（如果不存在）
        self.create_collection()

    def create_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except Exception as e:
            print(f"Collection '{self.collection_name}' does not exist, creating a new one...")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)  # 根据嵌入模型的维度设置大小
            )

    def load_txt_files(self, input_folder):
        """遍历文件夹，获取所有txt文件"""
        txt_files = []
        for dirpath, dirnames, filenames in os.walk(input_folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    txt_files.append(os.path.join(dirpath, filename))
        return txt_files

    def chunk_text(self, text, chunk_size=300, chunk_overlap=50):
        """
        使用 langchain 的 CharacterTextSplitter 进行文本分块
        支持按字符分割，并可设置重叠部分
        
        参数:
            text (str): 要分割的文本
            chunk_size (int): 每个块的最大长度（字符数）
            chunk_overlap (int): 块之间的重叠长度（字符数）
            
        返回:
            List[str]: 分割后的文本块列表
        """
        # 初始化分割器
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # 执行分割（返回 Document 对象列表）
        documents = text_splitter.create_documents([text])
        
        # 提取纯文本内容
        chunks = [doc.page_content for doc in documents]
        return chunks

    def text_to_vector(self, text):
        """将文本转换为向量"""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            embeddings = self.model(**inputs).last_hidden_state.mean(dim=1)
        return embeddings.squeeze().numpy()

    def save_to_qdrant(self, text_chunks, file_id):
        """将文本切割后的内容和向量存储到 Qdrant 中"""
        points = []
        for idx, chunk in enumerate(text_chunks):
            vector = self.text_to_vector(chunk)
            # 使用UUID作为点ID
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload={
                    "text": chunk,
                    "source_file": file_id,
                    "chunk_index": idx
                }
            ))
        self.client.upsert(collection_name=self.collection_name, points=points)

    def process_files(self, input_folder):
        """处理文件夹中的所有txt文件"""
        txt_files = self.load_txt_files(input_folder)
        for file_path in txt_files:
            print(f"Processing file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            chunks = self.chunk_text(content)
            self.save_to_qdrant(chunks, os.path.basename(file_path))