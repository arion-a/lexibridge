"""Offline ingestion: chunk local legal documents and compute embeddings
entirely on-device (ONNX multilingual MiniLM), so raw text never has to
leave the machine. Writes `my_manual_vector.json` locally (kept out of
git — see .gitignore) and, with --push, upserts *vectors only* (no text)
to the cloud Pinecone index.

Point --vault-dir at a locally synced copy of the legal vault (e.g. a
Google Drive Desktop / rclone mount of the client legal vault).

Usage:
    python embed_offline.py                # embed vault -> my_manual_vector.json
    python embed_offline.py --push         # also upsert vectors to Pinecone
"""

import argparse
import json
import re
import sys
import uuid
from pathlib import Path

import config
import embedding

CHUNK_TARGET_CHARS = 800
CHUNK_MIN_CHARS = 200

# Sentence terminators for both English (. ! ? ;) and Hindi (। ॥), so a
# chunk boundary never lands mid-sentence in either language.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;।॥])\s+")


def _read_documents(vault_dir: Path):
    for path in sorted(vault_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".txt", ".md"):
            yield path, path.read_text(encoding="utf-8", errors="ignore")


def _split_sentences(paragraph: str) -> list:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]


def chunk_document(text: str) -> list:
    """Chunk into ~CHUNK_TARGET_CHARS pieces without cutting a sentence in half."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        for sentence in _split_sentences(paragraph):
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) > CHUNK_TARGET_CHARS and len(current) >= CHUNK_MIN_CHARS:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def build_local_vector_store(vault_dir: Path) -> list:
    records = []
    for path, text in _read_documents(vault_dir):
        chunks = chunk_document(text)
        if not chunks:
            continue
        vectors = embedding.embed_texts(chunks)
        for page, (chunk_text, vector) in enumerate(zip(chunks, vectors), start=1):
            records.append({
                "id": str(uuid.uuid4()),
                "source_document": path.name,
                "page": page,
                "text": chunk_text,
                "vector": vector,
            })
    return records


def push_vectors_to_pinecone(records: list):
    from pinecone import Pinecone

    if not config.PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set")
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pc.Index(config.PINECONE_INDEX)

    # Zero text exposure: only the vector and a non-content locator go to
    # the cloud. The chunk text itself stays in the local vector store.
    upserts = [
        {
            "id": record["id"],
            "values": record["vector"],
            "metadata": {"source_document": record["source_document"], "page": record["page"]},
        }
        for record in records
    ]
    batch_size = 100
    for i in range(0, len(upserts), batch_size):
        index.upsert(vectors=upserts[i:i + batch_size])


def main():
    parser = argparse.ArgumentParser(description="Embed the local legal vault offline.")
    parser.add_argument("--vault-dir", default=config.LEGAL_VAULT_DIR)
    parser.add_argument("--out", default=config.LOCAL_VECTOR_STORE)
    parser.add_argument("--push", action="store_true", help="Also upsert vectors (no text) to Pinecone.")
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir)
    if not vault_dir.is_dir():
        print(f"Vault directory not found: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    records = build_local_vector_store(vault_dir)
    Path(args.out).write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Embedded {len(records)} chunks from {vault_dir} -> {args.out}")

    if args.push:
        push_vectors_to_pinecone(records)
        print(f"Pushed {len(records)} vectors (no text) to Pinecone index '{config.PINECONE_INDEX}'")


if __name__ == "__main__":
    main()
