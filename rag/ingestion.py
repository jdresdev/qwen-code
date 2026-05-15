from __future__ import annotations

from pathlib import Path

from rag.embedder import Embedder
from rag.vector_store import VectorStore

# File extensions we will attempt to read as text
TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".rb", ".php", ".swift", ".kt", ".sh", ".bash", ".yaml",
    ".yml", ".toml", ".json", ".xml", ".html", ".css", ".sql",
}

BATCH_SIZE = 32  # embed this many chunks per Ollama call


def ingest(
    path: str,
    collection: str,
    embedder: Embedder,
    store: VectorStore,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    working_dir: str = ".",
) -> str:
    """
    Load files from `path` (file or directory), chunk them, embed, and upsert into Qdrant.
    Returns a human-readable summary string.
    """
    p = Path(path)
    if not p.is_absolute():
        p = (Path(working_dir) / p).resolve()

    files = _collect_files(p)
    if not files:
        return f"No readable text files found at: {p}"

    total_chunks = 0
    ingested_files = 0

    for file in files:
        try:
            text = file.read_text(errors="replace")
        except Exception as e:
            continue

        chunks = _chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        if not chunks:
            continue

        source = str(file)
        # Remove old chunks for this file so re-ingestion is idempotent
        try:
            store.delete_by_source(collection, source)
        except Exception:
            pass

        chunk_dicts = [
            {"text": c, "source": source, "chunk_index": i}
            for i, c in enumerate(chunks)
        ]

        # Embed in batches
        for batch_start in range(0, len(chunk_dicts), BATCH_SIZE):
            batch = chunk_dicts[batch_start: batch_start + BATCH_SIZE]
            texts = [c["text"] for c in batch]
            vectors = embedder.embed_batch(texts)
            store.upsert(collection, batch, vectors)

        total_chunks += len(chunks)
        ingested_files += 1

    return (
        f"Ingested {ingested_files}/{len(files)} files into collection '{collection}'. "
        f"Total chunks: {total_chunks}."
    )


def retrieve(
    query: str,
    collection: str,
    embedder: Embedder,
    store: VectorStore,
    top_k: int = 5,
) -> str:
    """
    Embed `query` and return the top-k relevant chunks formatted for the LLM.
    """
    query_vector = embedder.embed(query)
    results = store.search(collection, query_vector, top_k=top_k)

    if not results:
        return f"No results found in collection '{collection}'."

    parts = [f"Retrieved {len(results)} relevant chunks:\n"]
    for i, r in enumerate(results, 1):
        parts.append(
            f"--- [{i}] {r.source} (chunk {r.chunk_index}, score {r.score:.3f}) ---\n{r.text}"
        )
    return "\n\n".join(parts)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _collect_files(p: Path) -> list[Path]:
    if p.is_file():
        return [p] if _is_text_file(p) else []
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.is_file() and _is_text_file(f))
    return []


def _is_text_file(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXTENSIONS


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks
