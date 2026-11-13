"""Hashing embedder for mock mode, and an OpenAI-compatible embedder."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"[a-z0-9]{3,}")
_STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "did",
    "say",
    "about",
    "what",
    "lot",
    "lots",
    "was",
    "were",
    "are",
    "its",
    "into",
}


def tokens(text: str) -> list[str]:
    return [token for token in _TOKEN.findall(text.lower()) if token not in _STOP]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def hash_embed(text: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def jaccard(left: list[str], right: list[str]) -> float:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Embedder(Protocol):
    kind: str

    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    kind = "mock"

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        return hash_embed(text, self.dimensions)


class OpenAIEmbedder:
    """POST {base}/embeddings. Used only when LLM_MODE=openai."""

    kind = "openai"

    def __init__(self, base_url: str, api_key: str, model: str, dimensions: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        import httpx

        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        vector: list[float] = response.json()["data"][0]["embedding"]
        if len(vector) != self.dimensions:
            raise RuntimeError(f"embedding length {len(vector)} does not match EMBEDDING_DIM={self.dimensions}")
        return vector
