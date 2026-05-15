from __future__ import annotations

from openai import OpenAI


class Embedder:
    """Produces embeddings via Ollama's /v1/embeddings endpoint."""

    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "nomic-embed-text") -> None:
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key="ollama")

    def embed(self, text: str) -> list[float]:
        """Embed a single string. Returns a float vector."""
        response = self._client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings in one API call."""
        if not texts:
            return []
        response = self._client.embeddings.create(input=texts, model=self.model)
        # Preserve order (Ollama returns in input order)
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    @property
    def dimension(self) -> int:
        """nomic-embed-text produces 768-dimensional vectors."""
        return 768
