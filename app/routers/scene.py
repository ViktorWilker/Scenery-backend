from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.embedding import get_embedding
from app.services.gemini import generate_scene
from app.services.vector_search import search_similar_sounds

router = APIRouter()

MIN_SCORE = 0.5
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
    candidates = search_similar_sounds(embedding)

    if not candidates:
        raise HTTPException(status_code=404, detail="Nenhum som encontrado")

    best_score = candidates[0].get("score", 0)
    if best_score < MIN_SCORE:
        raise HTTPException(status_code=422, detail="Prompt muito distante dos sons disponíveis")

    scene = generate_scene(request.prompt, candidates)

    url_map = {c["id"]: c["preview_url"] for c in candidates}
    for sound in scene["sounds"]:
        sound["preview_url"] = url_map.get(sound["id"], "")

    return scene

