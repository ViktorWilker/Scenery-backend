from app.db.mongo import sounds_collection
from app.services.embedding import get_embedding


def search_similar_sounds(embedding: list[float], top_k: int = 6) -> list[dict]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "description": 1,
                "preview_url": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    return list(sounds_collection.aggregate(pipeline))


def search_sounds_by_terms(terms: list[str], top_k_per_term: int = 3) -> list[dict]:
    seen_ids = set()
    results = []

    for term in terms:
        embedding = get_embedding(term)
        candidates = search_similar_sounds(embedding, top_k=top_k_per_term)
        for c in candidates:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                results.append(c)

    return results