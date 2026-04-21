from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sentence_transformers import SentenceTransformer
import os

# 配置常量
API_KEY = os.getenv("EMBED_API_KEY", "faying-secret-2026")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()
model = SentenceTransformer(os.getenv("EMBED_MODEL_DIR"))

async def get_api_key(header_key: str = Security(api_key_header)):
    if header_key == API_KEY:
        return header_key
    raise HTTPException(status_code=403, detail="Could not validate API Key")

app = FastAPI()

# 1. 在初始化时加载所有需要的模型
# 建议通过环境变量配置要启用的模型列表
models = {
    "bge-large": SentenceTransformer(os.getenv("BGE_LARGE_PATH")),
    "bge-small": SentenceTransformer(os.getenv("BGE_SMALL_PATH")),
}

@app.post("/embed/{model_name}")
async def embed(model_name: str, texts: list[str], token: str = Security(get_api_key)):
    # 2. 根据路径参数动态选择模型
    if model_name not in models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    vectors = models[model_name].encode(texts).tolist()
    return {"model": model_name, "vectors": vectors}