import os
import torch
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from transformers import AutoModel, AutoTokenizer, AutoModelForSpeechSeq2Seq, AutoProcessor

# ===================== 1. 配置定义 =====================
# 只有在列表里的模型才会被加载
# 格式：{"模型标识": {"path_env": "环境变量名", "type": "模型类型"}}
MODEL_CONFIG_REGISTRY = {
    "bge-large": {"env": "BGE_LARGE_PATH", "type": "text-embed"},
    "bge-small": {"env": "BGE_SMALL_PATH", "type": "text-embed"},
    "whisper": {"env": "WHISPER_PATH", "type": "speech-seq2seq"},
}

API_KEY = os.getenv("EMBED_API_KEY", "faying-secret-2026")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI(title="动态加载多模型服务")
device = "cuda" if torch.cuda.is_available() else "cpu"

# 全局容器
models = {}
tokenizers = {}
processors = {}

# ===================== 2. 动态加载逻辑 =====================
def load_enabled_models():
    print(f"--- 正在检测模型配置 (设备: {device}) ---")
    
    for model_id, config in MODEL_CONFIG_REGISTRY.items():
        model_path = os.getenv(config["env"])
        
        if not model_path:
            print(f"跳过 [{model_id}]: 未检测到环境变量 {config['env']}")
            continue
            
        try:
            print(f"正在加载 [{model_id}] 来自 {model_path}...")
            
            if config["type"] == "text-embed":
                tokenizers[model_id] = AutoTokenizer.from_pretrained(model_path)
                models[model_id] = AutoModel.from_pretrained(model_path).to(device)
                
            elif config["type"] == "speech-seq2seq":
                processors[model_id] = AutoProcessor.from_pretrained(model_path)
                models[model_id] = AutoModelForSpeechSeq2Seq.from_pretrained(model_path).to(device)
            
            print(f"成功加载 [{model_id}] ✅")
            
        except Exception as e:
            print(f"加载 [{model_id}] 失败 ❌: {str(e)}")

# 在应用启动时执行加载
load_enabled_models()

# ===================== 3. 统一接口逻辑 =====================
async def get_api_key(header_key: str = Security(api_key_header)):
    if header_key != API_KEY:
        raise HTTPException(status_code=403, detail="无效的 API Key")
    return header_key

@app.post("/embed/{model_name}")
async def embed(model_name: str, texts: list[str], _=Security(get_api_key)):
    # 自动检查模型是否已加载
    if model_name not in models or model_name not in tokenizers:
        raise HTTPException(status_code=404, detail=f"模型 {model_name} 未加载或不支持嵌入")

    tokenizer = tokenizers[model_name]
    model = models[model_name]

    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    # 均值池化
    embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy().tolist()
    return {"model": model_name, "vectors": embeddings}

@app.get("/models")
async def list_models(_=Security(get_api_key)):
    """方便前端查看当前激活了哪些模型"""
    return {
        "active_models": list(models.keys()),
        "device": device
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)