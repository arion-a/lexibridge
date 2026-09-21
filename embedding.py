"""Local, offline text embedding via ONNX multilingual MiniLM.

Runs entirely on-device (CPU, no PyTorch) so legal document text never has
to leave the local machine in order to be embedded — only the resulting
384-dim float vectors do. Shared by `embed_offline.py` (bulk ingestion) and
`vault.py` (embedding a live search query).
"""

import numpy as np
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

import config

_tokenizer = None
_model = None


def _load():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(config.EMBEDDING_MODEL)
        try:
            _model = ORTModelForFeatureExtraction.from_pretrained(config.EMBEDDING_MODEL)
        except Exception:
            # Xenova's ONNX exports commonly live under an "onnx/" subfolder.
            _model = ORTModelForFeatureExtraction.from_pretrained(config.EMBEDDING_MODEL, subfolder="onnx")
    return _tokenizer, _model


def _mean_pool(last_hidden_state: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    mask = attention_mask[..., None].astype(np.float32)
    summed = (last_hidden_state * mask).sum(axis=1)
    counts = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
    return summed / counts


def embed_texts(texts: list) -> list:
    """Embed a batch of texts locally. Returns one 384-dim unit vector per text."""
    tokenizer, model = _load()
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=256, return_tensors="np")
    outputs = model(**inputs)
    pooled = _mean_pool(outputs.last_hidden_state, inputs["attention_mask"])
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    normalized = pooled / np.clip(norms, a_min=1e-9, a_max=None)
    return normalized.tolist()


def embed_query(text: str) -> list:
    return embed_texts([text])[0]
