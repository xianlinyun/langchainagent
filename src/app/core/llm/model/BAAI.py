import os
from langchain_huggingface import HuggingFaceEmbeddings

# 建议手动指定模型存放路径，避免占用 C 盘
model_path = "./models/bge-large-zh-v1.5" 

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5",
    model_kwargs={'device': 'cuda'}, 
    encode_kwargs={'normalize_embeddings': True},
    cache_folder="./model_cache" # 缓存目录
)

# 针对 BGE v1.5 的 Query 增强
# 注意：在调用 retriever 时手动处理前缀更稳妥
def get_legal_query(user_input: str):
    return f"为法律咨询检索相关条文：{user_input}"