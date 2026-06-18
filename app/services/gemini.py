from google import genai
from app.config import settings

def build_prompt(user_prompt: str, candidates: list[dict]) -> str:
    sound_list = "\n".join(
        f"- id: {s['id']} | descrição: {s['description']}"
        for s in candidates
    )
    return f"""
Você é um compositor de ambientes sonoros.
O usuário descreveu uma cena e você deve montar um mix de sons para ela.

Sons disponíveis (use apenas estes):
{sound_list}

Responda APENAS com um JSON válido, sem markdown, sem texto extra:
{{
  "scene_name": "nome criativo e evocativo da cena (máx 5 palavras)",
  "mood": "2-3 adjetivos que descrevem o clima",
  "sounds": [
    {{ "id": "ID_DO_SOM", "volume": 0.0 a 1.0 }}
  ]
}}

Use entre 2 e 4 sons. O som principal com volume mais alto, secundários mais baixos.

Cena: {user_prompt}
""".strip()

def generate_scene(user_prompt: str, candidates: list[dict]) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(user_prompt, candidates)
    )

    raw = response.text.replace("```json", "").replace("```", "").strip()

    import json
    return json.loads(raw)