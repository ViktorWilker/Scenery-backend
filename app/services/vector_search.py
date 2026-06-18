from app.db.mongo import sounds_collection

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