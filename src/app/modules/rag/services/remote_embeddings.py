from __future__ import annotations

import asyncio
import json
import os
from typing import List
from urllib import error, request

import httpx
from langchain_core.embeddings import Embeddings


class RemoteEmbeddingService(Embeddings):
    """使用外部 HTTP 服务计算文本向量的 Embeddings 封装。

    默认会调用 docker-compose 里的 `embedding_api` 服务：
    - 基础地址优先读环境变量 EMBEDDING_API_BASE_URL
    - 默认值为 "http://embedding_api:8080"
    """

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url or os.getenv("EMBEDDING_API_BASE_URL", "http://embedding_api:8080")
        self.timeout = timeout

    # -------------------- 同步接口（兼容原有用法） --------------------

    # 单条查询向量（同步，满足 Embeddings 抽象基类要求）
    def embed_query(self, text: str) -> List[float]:
        data = self._post_json("/embed", {"text": text})
        vector = data.get("vector")
        if not isinstance(vector, list):
            raise ValueError(f"Invalid response from embedding service: {data!r}")
        return vector  # type: ignore[return-value]

    # 批量文档向量（同步）
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 目前服务端只实现了单条 /embed，这里简单循环调用；
        # 如需提速，可以在服务端增加 /embed_batch 接口，再在这里做一次请求。
        return [self.embed_query(t) for t in texts]

    # 内部 HTTP 辅助（同步）
    def _post_json(self, path: str, payload: dict) -> dict:
        url = self.base_url.rstrip("/") + path
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                resp_body = resp.read().decode("utf-8")
        except error.URLError as e:
            raise RuntimeError(f"Failed to call embedding service {url!r}: {e}") from e

        try:
            return json.loads(resp_body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from embedding service {url!r}: {resp_body!r}") from e

    # -------------------- 异步接口（推荐在 async 场景下使用） --------------------

    async def _apost_json(self, path: str, payload: dict) -> dict:
        """异步 HTTP POST，返回 JSON。"""

        url = self.base_url.rstrip("/") + path
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to call embedding service {url!r}: {e}") from e

        try:
            return resp.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from embedding service {url!r}: {resp.text!r}") from e

    async def aembed_query(self, text: str) -> List[float]:
        """异步单条向量查询。"""

        data = await self._apost_json("/embed", {"text": text})
        vector = data.get("vector")
        if not isinstance(vector, list):
            raise ValueError(f"Invalid response from embedding service: {data!r}")
        return vector  # type: ignore[return-value]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步批量向量查询，内部并发调用以提高吞吐。"""

        if not texts:
            return []

        tasks = [self.aembed_query(t) for t in texts]
        # 并发等待所有任务完成
        return await asyncio.gather(*tasks)
