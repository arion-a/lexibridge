"""Semantic search over the legal vault (Pinecone-backed precedent store)."""

from pinecone import Pinecone
import voyageai

import config

_pc = None
_index = None
_voyage = None


def _get_index():
    global _pc, _index
    if _index is None:
        if not config.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not set")
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
        _index = _pc.Index(config.PINECONE_INDEX)
    return _index


def _get_voyage():
    global _voyage
    if _voyage is None:
        if not config.VOYAGE_API_KEY:
            raise RuntimeError("VOYAGE_API_KEY is not set")
        _voyage = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _voyage


def embed_query(text: str) -> list:
    result = _get_voyage().embed([text], model=config.VOYAGE_MODEL, input_type="query")
    return result.embeddings[0]


def search_clauses(query: str, max_results: int = 4) -> list:
    index = _get_index()
    vector = embed_query(query)
    raw_response = index.query(vector=vector, top_k=max_results, include_metadata=True)

    results = []
    for match in raw_response.get("matches", []):
        metadata = match.get("metadata", {})
        results.append({
            "source_document": metadata.get("filename", "Unknown File"),
            "page": metadata.get("page_number", 1),
            "text_content": metadata.get("text", ""),
            "relevance_score": match.get("score"),
        })
    return results
