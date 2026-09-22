"""Text embedding via Voyage AI's hosted API.

Originally this loaded an ONNX model in-process (optimum + transformers),
but that pulled in a full ML stack heavy enough to OOM-kill the deployed
container on first real use. Since this deployment already sends document
text to the cloud (Pinecone) rather than keeping embedding strictly local,
there's no remaining reason to pay that memory cost — a hosted embeddings
API call is lighter and more reliable. voyage-law-2 is Voyage's
legal-domain model, a good fit for this vault's contract/precedent text.
"""

import voyageai

import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.VOYAGE_API_KEY:
            raise RuntimeError("VOYAGE_API_KEY is not set")
        _client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _client


def embed_texts(texts: list, input_type: str = "document") -> list:
    """Embed a batch of texts. `input_type` is "document" when ingesting,
    "query" when embedding a search query — Voyage optimizes each differently."""
    result = _get_client().embed(texts, model=config.VOYAGE_MODEL, input_type=input_type)
    return result.embeddings


def embed_query(text: str) -> list:
    return embed_texts([text], input_type="query")[0]
