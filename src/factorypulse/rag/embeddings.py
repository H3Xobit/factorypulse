"""Local embeddings. Prefer hashing encoder for offline/CI; optional bge-m3 later."""

from __future__ import annotations

import hashlib
import math
import re

import numpy as np

DIM = 384
_TOKEN = re.compile(r"[A-Za-z0-9\-]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def embed_text(text: str, dim: int = DIM) -> list[float]:
    """Deterministic bag-of-tokens hashing embedder (unit L2)."""
    vec = np.zeros(dim, dtype=np.float64)
    tokens = _tokenize(text)
    if not tokens:
        vec[0] = 1.0
        return vec.astype(np.float32).tolist()
    for tok in tokens:
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(float(np.dot(vec, vec))) + 1e-12
    vec /= norm
    return vec.astype(np.float32).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [embed_text(t) for t in texts]
