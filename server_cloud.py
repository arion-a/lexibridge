"""LexiBridge cloud bridge — deployed remotely (e.g. Railway).

Accepts an already-computed query vector and looks it up in Pinecone. It
never performs embedding itself and never receives or stores raw document
text — only float coordinates cross this boundary. See SPECIFICATION.md.
"""

import json
import os

from fastmcp import FastMCP
from pinecone import Pinecone

import config

mcp = FastMCP("LexiBridge-Cloud-Vault")

_pc = None
_index = None


def _get_index():
    global _pc, _index
    if _index is None:
        if not config.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY is not set")
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
        _index = _pc.Index(config.PINECONE_INDEX)
    return _index


@mcp.tool()
def query_vault_with_precomputed_vector(vector: list, top_k: int = 4) -> str:
    """
    Query the remote Pinecone vault with an already-computed embedding
    vector. Returns a JSON list of {id, source_document, page, score}.

    No document text is ever stored in this index, so none is returned
    here either — callers re-hydrate text from their own local vector
    store, keyed by `id`.
    """
    try:
        index = _get_index()
        raw_response = index.query(vector=vector, top_k=top_k, include_metadata=True)
        matches = []
        for match in raw_response.get("matches", []):
            metadata = match.get("metadata", {})
            matches.append({
                "id": match.get("id"),
                "source_document": metadata.get("source_document", "Unknown File"),
                "page": metadata.get("page", 1),
                "score": match.get("score"),
            })
        return json.dumps(matches, indent=2)
    except Exception as e:
        return f"Cloud lookup error: {e}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)
