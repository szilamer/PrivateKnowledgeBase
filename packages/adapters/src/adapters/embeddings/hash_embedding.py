import hashlib
import struct


class HashEmbeddingProvider:
    """Deterministic local embeddings for offline dev and e2e smoke tests."""

    def __init__(self, *, dimension: int = 1536) -> None:
        self.model = "hash-embedding-dev"
        self.dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector: list[float] = []
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        while len(vector) < self.dimension:
            for index in range(0, len(seed), 4):
                if len(vector) >= self.dimension:
                    break
                chunk = seed[index : index + 4]
                if len(chunk) < 4:
                    chunk = chunk.ljust(4, b"\0")
                value = struct.unpack(">I", chunk)[0] / (2**32)
                vector.append(value * 2 - 1)
            seed = hashlib.sha256(seed).digest()
        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0:
            return vector
        return [value / norm for value in vector]
