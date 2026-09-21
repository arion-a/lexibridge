"""Legal vault search.

Embeds the query locally, asks the remote cloud bridge (server_cloud.py)
to match it against Pinecone by vector only, then re-hydrates the actual
clause text from the local vector store built by embed_offline.py — so
the text a caller reads never had to be stored or transmitted to the
cloud to get there.
"""

import json
from pathlib import Path

from fastmcp import Client

import config
import embedding

_local_records_by_id = None


def _load_local_records() -> dict:
    global _local_records_by_id
    if _local_records_by_id is None:
        path = Path(config.LOCAL_VECTOR_STORE)
        if not path.exists():
            raise RuntimeError(
                f"{path} not found — run `python embed_offline.py --push` first "
                "to build the local vault and populate the cloud index."
            )
        records = json.loads(path.read_text(encoding="utf-8"))
        _local_records_by_id = {record["id"]: record for record in records}
    return _local_records_by_id


def _parse_matches(result) -> list:
    content = getattr(result, "data", None)
    if content is None:
        content = result.content[0].text
    return content if isinstance(content, list) else json.loads(content)


async def search_clauses(query: str, max_results: int = 4) -> list:
    if not config.CLOUD_SERVER_URL:
        raise RuntimeError("CLOUD_SERVER_URL is not set")

    vector = embedding.embed_query(query)
    local_records = _load_local_records()

    async with Client(config.CLOUD_SERVER_URL) as client:
        result = await client.call_tool(
            "query_vault_with_precomputed_vector",
            {"vector": vector, "top_k": max_results},
        )
    matches = _parse_matches(result)

    results = []
    for match in matches:
        record = local_records.get(match.get("id"), {})
        results.append({
            "source_document": match.get("source_document", "Unknown File"),
            "page": match.get("page", 1),
            "text_content": record.get("text", ""),
            "relevance_score": match.get("score"),
        })
    return results
