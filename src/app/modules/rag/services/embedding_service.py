from fastapi import FastAPI
from langchain_community.embeddings import HuggingFaceEmbeddings
import uvicorn

app = FastAPI()

# 【关键】在全局作用域加载模型，只加载一次
print("--- 正在加载 BGE 模型到显存... ---")
model_path = "/app/model_cache/BAAI/bge-large-zh-v1.5"
embeddings = HuggingFaceEmbeddings(
    model_name=model_path,
    model_kwargs={'device': 'cpu'} # 确保用到你的 960
)

@app.post("/embed")
async def embed_text(payload: dict):
    text = payload.get("text", "")
    # 这里的调用是极速的，因为模型已经在显存里了
    vector = await embeddings.aembed_query(text)
    return {"vector": vector}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)