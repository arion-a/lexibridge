"""Legal vault: on-device embedding plus Pinecone storage/search, all
running inside this same deployed container.

Note: this collapses the local-machine/cloud-bridge split described in
SPECIFICATION.md into a single cloud service, by explicit choice — see
README.md for the tradeoff (document text now lives in Pinecone, not only
on a local machine).

The Pinecone index is created automatically on first use if it doesn't
exist yet — no manual dashboard step required.
"""

import time
import uuid

import config
import embedding

_pc = None
_index = None

# All current Voyage embedding models default to 1024 dimensions unless an
# explicit output_dimension is requested (we don't request one). Kept as a
# lookup rather than a bare constant so a future model with a different
# default is easy to add.
_VOYAGE_DIMENSIONS = {
    "voyage-law-2": 1024,
    "voyage-finance-2": 1024,
    "voyage-4-large": 1024,
    "voyage-4": 1024,
    "voyage-4-lite": 1024,
    "voyage-4-nano": 1024,
    "voyage-code-4": 1024,
}


def _embedding_dimension() -> int:
    return _VOYAGE_DIMENSIONS.get(config.VOYAGE_MODEL, 1024)


def _existing_index_names(pc) -> set:
    try:
        return set(pc.list_indexes().names())
    except AttributeError:
        return {idx["name"] for idx in pc.list_indexes()}


def _index_dimension(description) -> int:
    try:
        return description.dimension
    except AttributeError:
        return description["dimension"]


def _get_index():
    global _pc, _index
    if _index is None:
        from pinecone import Pinecone, ServerlessSpec

        if not config.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not set")
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)

        target_dimension = _embedding_dimension()

        if config.PINECONE_INDEX not in _existing_index_names(_pc):
            _pc.create_index(
                name=config.PINECONE_INDEX,
                dimension=target_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not _pc.describe_index(config.PINECONE_INDEX).status["ready"]:
                time.sleep(1)
        else:
            actual_dimension = _index_dimension(_pc.describe_index(config.PINECONE_INDEX))
            if actual_dimension != target_dimension:
                raise RuntimeError(
                    f"Pinecone index '{config.PINECONE_INDEX}' has dimension {actual_dimension}, "
                    f"but {config.VOYAGE_MODEL} produces {target_dimension}-dim vectors. "
                    "Pinecone can't change an index's dimension in place — delete it and this "
                    "server will recreate it correctly on the next call: run this once in "
                    "Railway's Console tab: python3 -c \"from pinecone import Pinecone; import "
                    f"os; Pinecone(api_key=os.environ['PINECONE_API_KEY']).delete_index('{config.PINECONE_INDEX}')\""
                )

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
