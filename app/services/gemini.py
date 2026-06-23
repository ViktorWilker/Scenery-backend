from google import genai
from app.config import settings
import json

client = genai.Client(api_key=settings.gemini_api_key)


def build_prompt(user_prompt: str, candidates: list[dict], knowledge_context: str) -> str:
    sound_list = "\n".join(
        f"- id: {s['id']} | description: {s['description']}"
        for s in candidates
    )
    return f"""You are an expert sound designer composing immersive soundscapes.

Use the following sound design knowledge to guide your choices:
{knowledge_context}

---

Available sounds (use ONLY these):
{sound_list}

Respond ONLY with valid JSON, no markdown, no extra text:
{{
  "scene_name": "creative evocative name (max 5 words)",
  "mood": "2-3 adjectives describing the atmosphere",
  "sounds": [
    {{ "id": "SOUND_ID", "volume": 0.0 to 1.0 }}
  ]
}}

Rules:
- Use between 2 and 4 sounds
- Main sound gets highest volume, supporting sounds get lower volumes
- Apply layering principles: foreground (high volume), midground (medium), background (low)
- Prefer non-obvious combinations when the knowledge above supports it

Scene: {user_prompt}
""".strip()


def generate_scene(user_prompt: str, candidates: list[dict], knowledge_context: str) -> dict:
    response = client.models.generate_content(
        model="gemini-1.5-flash-latest",
        contents=build_prompt(user_prompt, candidates, knowledge_context)
    )
    raw = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)