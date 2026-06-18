from google import genai
from app.config import settings

def get_embedding(text: str) -> list[float]:
    client = genai.Client(api_key=settings.gemini_api_key)
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents = text,
        )
    return result.embeddings[0].values