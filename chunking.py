"""Shared text chunking for the legal vault.

Splits text into passages that preserve sentence boundaries in both
English and Hindi, so a chunk never cuts a sentence in half. Used by
embed_offline.py (bulk ingestion) and the ingest_document MCP tool.
"""

import re

CHUNK_TARGET_CHARS = 800
CHUNK_MIN_CHARS = 200

# Sentence terminators for both English (. ! ? ;) and Hindi (। ॥).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;।॥])\s+")


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
