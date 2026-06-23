import ssl
import certifi
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import time
import json
import requests
from app.services.embedding import get_embedding
from app.services.knowledge_search import search_knowledge, format_for_prompt
from app.db.mongo import sounds_collection
from app.config import settings
from google import genai

client = genai.Client(api_key=settings.gemini_api_key)

def get_existing_sounds() -> list[dict]:
    return list(sounds_collection.find({}, {"_id": 0, "id": 1, "description": 1}))

def identify_gaps(existing: list[dict], knowledge_context: str) -> list[dict]:
    existing_list = "\n".join(f"- {s['id']}: {s['description']}" for s in existing)

    prompt = f"""You are an expert sound designer reviewing a sound catalog for an ambient soundscape app.

Sound design knowledge to guide your analysis:
{knowledge_context}

---

Current catalog ({len(existing)} sounds):
{existing_list}

---

Identify gaps in this catalog — sound types that are missing but would make scenes more immersive.
Focus especially on non-obvious elements: midground and background layers that naive searches miss.

Respond ONLY with a valid JSON array, no markdown, no extra text:
[
  {{
    "id": "unique_snake_case_id",
    "description": "short english description for freesound search (3-6 words)",
    "category": "category name",
    "layer": "foreground | midground | background"
  }}
]

Rules:
- Suggest between 40 and 60 new sounds
- id must be unique and not already in the catalog
- description must be concrete and searchable on Freesound
- Prioritize non-obvious elements that add credibility to a scene
- Avoid sounds with intelligible human voice
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    raw = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def search_freesound(query: str, n: int = 5) -> list[dict]:
    url = "https://freesound.org/apiv2/search/text/"
    
    queries_to_try = [
        query,
        " ".join(query.split()[:3]),  # primeiras 3 palavras
        " ".join(query.split()[:2]),  # primeiras 2 palavras
    ]
    seen = set()
    queries_to_try = [q for q in queries_to_try if not (q in seen or seen.add(q))]

    for q in queries_to_try:
        params = {
            "query": q,
            "token": settings.freesound_api_key,
            "fields": "id,name,previews,duration",
            "filter": "duration:[15 TO 120]",
            "page_size": n
        }
        response = requests.get(url, params=params)
        results = response.json().get("results", [])
        if results:
            if q != query:
                print(f"  (fallback query: '{q}')")
            return results
        time.sleep(0.3)

    return []


def pick_best(results: list[dict]) -> dict | None:

    if not results:
        return None
    return max(results, key=lambda r: r.get("duration", 0))

def insert_sound(sound_meta: dict, preview_url: str):
    embedding = get_embedding(sound_meta["description"])
    doc = {
        "id": sound_meta["id"],
        "description": sound_meta["description"],
        "tags": [sound_meta["category"], sound_meta["layer"]],
        "preview_url": preview_url,
        "embedding": embedding
    }
    sounds_collection.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)

def run():
    print("=== Expand Catalog ===\n")

    existing = get_existing_sounds()
    print(f"Catálogo atual: {len(existing)} sons\n")

    knowledge_chunks = search_knowledge("sound design layering gaps ambience scenes")
    knowledge_context = format_for_prompt(knowledge_chunks)

    print("Identificando lacunas com Gemini...")
    gaps = identify_gaps(existing, knowledge_context)
    print(f"{len(gaps)} sons sugeridos\n")

    existing_ids = {s["id"] for s in existing}
    gaps = [g for g in gaps if g["id"] not in existing_ids]
    print(f"{len(gaps)} novos após filtrar ids já existentes\n")


    existing_db_ids = {doc["id"] for doc in sounds_collection.find({}, {"_id": 0, "id": 1})}
    gaps = [g for g in gaps if g["id"] not in existing_db_ids]
    print(f"{len(gaps)} novos após filtrar banco atual\n")
    
    inserted = 0
    skipped = 0

    for gap in gaps:
        print(f"[{gap['layer']}] {gap['id']} — buscando '{gap['description']}'...")

        results = search_freesound(gap["description"], n=5)
        best = pick_best(results)

        if not best:
            print(f"   resultado mesmo com fallback, pulando\n")
            skipped += 1
            continue

        preview_url = best["previews"]["preview-hq-mp3"]
        insert_sound(gap, preview_url)
        inserted += 1
        print(f"  ok ({best['duration']:.0f}s)\n")

        time.sleep(0.5)

    print(f"=== Concluído: {inserted} inseridos, {skipped} pulados ===")
    print(f"Total no catálogo: {sounds_collection.count_documents({})}")

run()