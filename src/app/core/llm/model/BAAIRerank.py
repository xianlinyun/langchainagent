from FlagEmbedding import FlagReranker

# 选一个合适的模型（多语言/中文推荐）
# 常见：'BAAI/bge-reranker-large', 'BAAI/bge-reranker-base', 'BAAI/bge-reranker-v2-m3'
model_name = "BAAI/bge-reranker-large"

# use_fp16=True 适合有 GPU 的环境；CPU 可以改成 False
reranker = FlagReranker(model_name, use_fp16=False)

def rerank(query: str, passages: list[str]) -> list[tuple[str, float]]:
    # 返回每个 passage 的分数（越大越相关）
    scores = reranker.compute_score([(query, p) for p in passages])
    # 打包并按分数降序排序
    ranked = sorted(zip(passages, scores), key=lambda x: x[1], reverse=True)
    return ranked

if __name__ == "__main__":
    query = "扫地机器人一直绕圈是怎么回事？"
    docs = [
        "扫地机器人出现绕圈，多与传感器污染或轮子打滑有关。",
        "选购扫地机器人时，要关注吸力、电池容量等参数。",
        "洗地机适用于硬质地面清洁，与扫地机器人功能不同。"
    ]
    for doc, score in rerank(query, docs):
        print(f"{score:.4f}\t{doc}")