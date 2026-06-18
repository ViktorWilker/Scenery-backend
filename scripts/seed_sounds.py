import time
import requests
from app.services.embedding import get_embedding
from pymongo import MongoClient
from app.config import settings 
from google import genai
from google.genai import types


SOUNDS = [
    {"id": "rain_light",       "description": "light rain ambience",          "tags": ["natureza", "chuva", "relaxamento"]},
    {"id": "rain_heavy",       "description": "heavy rain storm",       "tags": ["natureza", "chuva", "intenso"]},
    {"id": "wind_soft",        "description": "soft gentle wind",              "tags": ["natureza", "vento", "relaxamento"]},
    {"id": "wind_howling",     "description": "strong howling wind",           "tags": ["natureza", "vento", "intenso"]},
    {"id": "thunder_distant",  "description": "distant thunder rumble",        "tags": ["natureza", "chuva", "intenso"]},
    {"id": "fire_crackling",   "description": "crackling fire campfire",       "tags": ["natureza", "fogo", "aconchego"]},
    {"id": "river_flowing",    "description": "flowing river stream water",    "tags": ["natureza", "água", "relaxamento"]},
    {"id": "ocean_waves",      "description": "ocean waves beach ambience",    "tags": ["natureza", "água", "relaxamento"]},
    {"id": "forest_birds",     "description": "forest birds chirping nature",  "tags": ["natureza", "floresta", "dia"]},
    {"id": "night_crickets",   "description": "crickets night insects",        "tags": ["natureza", "floresta", "noite"]},
    {"id": "cafe_ambience",    "description": "coffee shop cafe chatter",      "tags": ["urbano", "café", "foco"]},
    {"id": "city_traffic",     "description": "city traffic urban noise",      "tags": ["urbano", "cidade"]},
    {"id": "train_rolling",    "description": "train locomotive sounds",        "tags": ["urbano", "transporte", "viagem"]},
    {"id": "subway_station",   "description": "subway metro station ambience", "tags": ["urbano", "transporte"]},
    {"id": "crowd_murmur",     "description": "crowd murmur people talking",   "tags": ["urbano", "pessoas"]},
    {"id": "fireplace_indoor", "description": "indoor fireplace crackling",    "tags": ["interior", "fogo", "aconchego"]},
    {"id": "library_quiet",    "description": "quiet library page turning",    "tags": ["interior", "silêncio", "foco"]},
    {"id": "clock_ticking",    "description": "old clock ticking",             "tags": ["interior", "silêncio"]},
    {"id": "vinyl_crackle",    "description": "vinyl record player crackle",   "tags": ["interior", "música", "nostalgia"]},
    {"id": "space_drone",      "description": "space drone deep ambient",      "tags": ["fantasia", "espaço", "meditação"]},
    {"id": "cave_echo",        "description": "cave echo water drops",         "tags": ["fantasia", "natureza", "misterioso"]},
    {"id": "tavern_ambience",  "description": "pub crowd background noise",   "tags": ["fantasia", "medieval", "agitado"]},
]

def search_freesound(query: str) -> str | None:
    url = "https://freesound.org/apiv2/search/text/"
    params = {
        "query": query,
        "token": settings.freesound_api_key,
        "fields": "id,name,previews",
        "filter": "duration:[10 TO 120]",
        "page_size": 1
    }
    response = requests.get(url, params = params)
    results = response.json().get("results", [])
    if not results:
        return None
    return results[0]["previews"]["preview-hq-mp3"]

def run():    
    from app.db.mongo import sounds_collection
    sounds_collection.delete_many({})
    
    docs = []
    for sound in SOUNDS:
        print(f"processando: {sound['id']}")
        
        preview_url = search_freesound(sound['description'])
        if not preview_url:
            print(f" sem resultado no freesounds, pulando")
            continue
        
        embedding = get_embedding(sound["description"])
        
        docs.append({
            "id": sound["id"],
            "description": sound["description"],
            "tags": sound["tags"],
            "preview_url": preview_url,
            "embedding": embedding
        })
        
        print(f"Ok")
        time.sleep(0.5)
        
    sounds_collection.insert_many(docs)
    print(f"\n{len(docs)} sons inseridos com sucesso")
    
run()