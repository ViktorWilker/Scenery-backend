from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.embedding import get_embedding
from app.services.gemini import generate_scene
from app.services.vector_search import search_similar_sounds
from app.services.knowledge_search import search_knowledge, format_for_prompt

router = APIRouter()

MIN_PROMPT_LENGTH = 5


class SceneRequest(BaseModel):
    prompt: str


def is_valid_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if len(stripped) < MIN_PROMPT_LENGTH:
        return False
    if stripped.isdigit():
        return False
    if len(set(stripped)) < 3:
        return False
    return True


@router.post("/scene")
async def create_scene(request: SceneRequest):
    if not is_valid_prompt(request.prompt):
        raise HTTPException(status_code=400, detail="Prompt inválido")

    embedding = get_embedding(request.prompt)
    candidates = search_similar_sounds(embedding, top_k=15)

    if not candidates:
        raise HTTPException(status_code=404, detail="Nenhum som encontrado")

    knowledge_chunks = search_knowledge(request.prompt)
    knowledge_context = format_for_prompt(knowledge_chunks)

    scene = generate_scene(request.prompt, candidates, knowledge_context)

    url_map = {c["id"]: c["preview_url"] for c in candidates}
    for sound in scene["sounds"]:
        sound["preview_url"] = url_map.get(sound["id"], "")

    return scene