from __future__ import annotations

import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FilterSelector,
    FieldCondition,
    MatchValue,
)


@dataclass
class SearchResult:
    text: str
    source: str       # file path
    score: float
    chunk_index: int


class VectorStore:
    """
    Qdrant wrapper. Supports three modes via `url` config:
      - ":memory:"           → in-memory (no persistence, good for testing)
      - "./qdrant_data"      → local file storage (default)
      - "http://host:6333"   → remote Qdrant server
    """

    def __init__(self, url: str = "./qdrant_data", dimension: int = 768) -> None:
        self.dimension = dimension
        if url == ":memory:":
            self._client = QdrantClient(":memory:")
        elif url.startswith("http://") or url.startswith("https://"):
            self._client = QdrantClient(url=url)
        else:
            self._client = QdrantClient(path=url)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(self, name: str) -> None:
        """Create the collection if it doesn't exist yet."""
        existing = {c.name for c in self._client.get_collections().collections}
        if name not in existing:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )

    def delete_collection(self, name: str) -> bool:
        """Delete a collection. Returns True if it existed."""
        try:
            self._client.delete_collection(name)
            return True
        except Exception:
            return False

    def list_collections(self) -> list[str]:
        return [c.name for c in self._client.get_collections().collections]

    def collection_count(self, name: str) -> int:
        """Number of points in a collection."""
        try:
            info = self._client.get_collection(name)
            return info.vectors_count or 0
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(self, collection: str, chunks: list[dict], vectors: list[list[float]]) -> int:
        """
        Insert or update points.

        `chunks` must have keys: text, source, chunk_index
        Returns number of points upserted.
        """
        self.ensure_collection(collection)
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk, vec in zip(chunks, vectors)
        ]
        self._client.upsert(collection_name=collection, points=points)
        return len(points)

    def delete_by_source(self, collection: str, source: str) -> None:
        """Remove all chunks that came from a specific file path."""
        self._client.delete(
            collection_name=collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="source", match=MatchValue(value=source))]
                )
            ),
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(self, collection: str, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """Return the top-k most similar chunks."""
        try:
            hits = self._client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
        except Exception:
            return []

        return [
            SearchResult(
                text=hit.payload["text"],
                source=hit.payload["source"],
                score=hit.score,
                chunk_index=hit.payload.get("chunk_index", 0),
            )
            for hit in hits
        ]
