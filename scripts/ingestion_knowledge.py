from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
load_dotenv()

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "sound_design_knowledge"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_BATCH_SIZE = 20

_SOURCE_PRIMARY_RE = re.compile( r"\*\*(?:Source|Fonte)[:]?\*\*\s*"
    r"(?P<citation>.*?(?:Chapters?|Cap[íi]tulos?)\s+\d+(?:\s*(?:,|and|e)\s*\d+)*)",
    re.IGNORECASE,
)
_SOURCE_FALLBACK_RE = re.compile(
    r"\*\*(?:Source|Fonte)[:]?\*\*\s*(?P<citation>[^\n]+?)(?=\n|$)",
    re.IGNORECASE,
)
_LOW_PRIORITY_START_RE = re.compile(
    r"^#.*LOW PRIORITY(?!.*END).*$", re.IGNORECASE | re.MULTILINE
)
_LOW_PRIORITY_END_RE = re.compile(
    r"^#.*END OF LOW PRIORITY.*$", re.IGNORECASE | re.MULTILINE
)


def extract_source_citation(body: str) -> str | None:
    match = _SOURCE_PRIMARY_RE.search(body) or _SOURCE_FALLBACK_RE.search(body)
    return match.group("citation").strip() if match else None

def clean_body(body: str) -> str:
    cleaned = _SOURCE_PRIMARY_RE.sub("", body)
    cleaned = _SOURCE_FALLBACK_RE.sub("", cleaned)
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def split_into_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    level = None
    for line in lines:
        if line.startswith("#### "):
            level = "#### "
            break
        if line.startswith("## "):
            level = "## "
            break
    if level is None:
        return [("Untitled", text.strip())] if text.strip() else []

    sections, heading, body_lines = [], None, []
    for line in lines:
        if line.startswith(level):
            if heading is not None:
                sections.append((heading, "\n".join(body_lines).strip()))
            heading = re.sub(r"^\d+\\?\.\s*", "", line[len(level):].strip())
            body_lines = []
        elif heading is not None:
            body_lines.append(line)
    if heading is not None:
        sections.append((heading, "\n".join(body_lines).strip()))
    return [(h, b) for h, b in sections if b]


def parse_file(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")

    starts = [(m.start(), m.end(), True) for m in _LOW_PRIORITY_START_RE.finditer(raw)]
    ends = [(m.start(), m.end(), False) for m in _LOW_PRIORITY_END_RE.finditer(raw)]
    dividers = sorted(starts + ends, key=lambda d: d[0])

    spans: list[tuple[str, bool]] = []
    if not dividers:
        spans.append((raw, False))
    else:
        cursor = 0
        current_priority = False
        for d_start, d_end, sets_low_priority in dividers:
            spans.append((raw[cursor:d_start], current_priority))
            current_priority = sets_low_priority
            cursor = d_end
        spans.append((raw[cursor:], current_priority))

    chunks: list[dict] = []
    chunk_idx = 0
    for span_text, is_low_priority in spans:
        for heading, body in split_into_sections(span_text):
            chunk_text = f"{heading}\n\n{clean_body(body)}"
            chunks.append(
                {
                    "id": f"{path.stem}__{chunk_idx:03d}",
                    "text": chunk_text,
                    "heading": heading,
                    "source_file": path.name,
                    "source_citation": extract_source_citation(body),
                    "low_priority": is_low_priority,
                }
            )
            chunk_idx += 1
    return chunks


def parse_knowledge_dir(knowledge_dir: Path) -> list[dict]:
    all_chunks: list[dict] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        all_chunks.extend(parse_file(path))
    return all_chunks


def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        embeddings.extend([e.values for e in result.embeddings])
        print(f"  embedded {min(i + EMBEDDING_BATCH_SIZE, len(texts))}/{len(texts)} chunks")
        if i + EMBEDDING_BATCH_SIZE < len(texts):
            time.sleep(0.5)

    return embeddings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--knowledge-dir", type=Path, default=KNOWLEDGE_DIR)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: set GEMINI_API_KEY before running this script.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing knowledge base from {args.knowledge_dir} ...")
    chunks = parse_knowledge_dir(args.knowledge_dir)
    if not chunks:
        print(f"ERROR: no .md files found in {args.knowledge_dir}", file=sys.stderr)
        sys.exit(1)

    n_low = sum(c["low_priority"] for c in chunks)
    n_sourced = sum(bool(c["source_citation"]) for c in chunks)
    print(f"Parsed {len(chunks)} chunks from {len(list(args.knowledge_dir.glob('*.md')))} files "
          f"({n_low} low_priority, {n_sourced} with source citation)\n")

    print(f"Generating embeddings via {EMBEDDING_MODEL} ...")
    embeddings = embed_texts([c["text"] for c in chunks], api_key)
    print(f"Generated {len(embeddings)} embeddings\n")

    client = chromadb.CloudClient(
    tenant=os.environ["CHROMA_TENANT"],
    database=os.environ["CHROMA_DATABASE"],
    api_key=os.environ["CHROMA_API_KEY"],
    )
    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection '{COLLECTION_NAME}' (--reset)")
        except Exception:
            pass

    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_file": c["source_file"],
                "heading": c["heading"],
                "low_priority": c["low_priority"],
                **({"source_citation": c["source_citation"]} if c["source_citation"] else {}),
            }
            for c in chunks
        ],
    )

    print(f"Done. Collection '{COLLECTION_NAME}' at {CHROMA_PERSIST_DIR} now has {collection.count()} chunks.")


if __name__ == "__main__":
    main()
