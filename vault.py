"""Legal vault: on-device embedding plus Pinecone storage/search, all
running inside this same deployed container.

Note: this collapses the local-machine/cloud-bridge split described in
SPECIFICATION.md into a single cloud service, by explicit choice — see
README.md for the tradeoff (document text now lives in Pinecone, not only
on a local machine).
"""

import uuid

import config
import embedding

_pc = None
_index = None


def _get_index():
    global _pc, _index
    if _index is None:
        from pinecone import Pinecone

        if not config.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not set")
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
        _index = _pc.Index(config.PINECONE_INDEX)
    return _index


def ingest_chunks(source_document: str, chunks: list) -> int:
    if not chunks:
        return 0
    vectors = embedding.embed_texts(chunks)
    index = _get_index()
    upserts = [
        {
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": {"source_document": source_document, "page": page, "text": chunk_text},
        }
        for page, (chunk_text, vector) in enumerate(zip(chunks, vectors), start=1)
    ]
    batch_size = 100
    for i in range(0, len(upserts), batch_size):
        index.upsert(vectors=upserts[i:i + batch_size])
    return len(upserts)


def ingest_document(source_document: str, text: str) -> int:
    import chunking

    return ingest_chunks(source_document, chunking.chunk_document(text))


def search_clauses(query: str, max_results: int = 4) -> list:
    index = _get_index()
    vector = embedding.embed_query(query)
    raw_response = index.query(vector=vector, top_k=max_results, include_metadata=True)

    results = []
    for match in raw_response.get("matches", []):
        metadata = match.get("metadata", {})
        results.append({
            "source_document": metadata.get("source_document", "Unknown File"),
            "page": metadata.get("page", 1),
            "text_content": metadata.get("text", ""),
            "relevance_score": match.get("score"),
        })
    return results
