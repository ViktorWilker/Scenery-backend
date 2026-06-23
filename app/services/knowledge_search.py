from __future__ import annotations

import os
import chromadb
from app.config import settings

COLLECTION_NAME = "sound_design_knowledge"
EMBEDDING_MODEL = "gemini-embedding-001"

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.CloudClient(
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
            api_key=settings.chroma_api_key
        )
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _embed_query(query: str) -> list[float]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values


def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    collection = get_collection()
    embedding = _embed_query(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where={"low_priority": {"$ne": True}},
        include=["documents", "metadatas"]
    )

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "text": doc,
            "heading": meta.get("heading", ""),
            "source_citation": meta.get("source_citation", "")
        })

    return chunks


def format_for_prompt(chunks: list[dict]) -> str:
    if not chunks:
        return "No sound design knowledge available."

    lines = []
    for chunk in chunks:
        if chunk["heading"]:
            lines.append(f"### {chunk['heading']}")
        lines.append(chunk["text"])
        if chunk["source_citation"]:
            lines.append(f"Source: {chunk['source_citation']}")
        lines.append("")

    return "\n".join(lines).strip()