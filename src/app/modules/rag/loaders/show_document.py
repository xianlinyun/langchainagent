

from pathlib import Path

import chromadb

from app.core.config import settings


def show_document(category: setattr, limit: int = 10):
    persist_dir = Path(settings.chroma.persist_directory)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_collection(name=settings.chroma.collection_name)

    data = collection.get(
        where={"category": category},
        limit=limit,
        include=["embeddings", "metadatas", "documents"],
    )

    count = len(data.get("ids", []))
    print(f"collection={settings.chroma.collection_name}, category={category}, records={count}")
    metadatas = data.get("metadatas") or []
    embeddings = data.get("embeddings")
    for idx, doc in enumerate(data.get("documents", []), start=1):
        metadata = metadatas[idx - 1] if idx - 1 < len(metadatas) else {}
        embedding = embeddings[idx - 1] if embeddings is not None and idx - 1 < len(embeddings) else []
        vector_dim = len(embedding) if embedding is not None else 0
        preview = (doc or "")[:120].replace("\n", " ")
        print(f"[{idx}] dim={vector_dim}, metadata={metadata}")
        print(f"    content={preview}...")

    return data


if __name__ == "__main__":
    show_document("law/civil/labor")