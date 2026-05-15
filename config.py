from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "qwen-code" / "config.json"

DEFAULTS = {
    "model": "qwen2.5-coder:7b",
    "base_url": "http://localhost:11434/v1",
    "temperature": 0.1,
    "max_tokens": 8192,
    "context_limit": 28000,  # tokens before truncating history
    "bash_timeout": 30,      # seconds
    "auto_approve_reads": True,
    # RAG
    "embed_model": "nomic-embed-text",
    "qdrant_url": "http://localhost:6333",
    "rag_collection": "default",
    "rag_chunk_size": 500,
    "rag_chunk_overlap": 50,
}


@dataclass
class Config:
    model: str = DEFAULTS["model"]
    base_url: str = DEFAULTS["base_url"]
    temperature: float = DEFAULTS["temperature"]
    max_tokens: int = DEFAULTS["max_tokens"]
    context_limit: int = DEFAULTS["context_limit"]
    bash_timeout: int = DEFAULTS["bash_timeout"]
    auto_approve_reads: bool = DEFAULTS["auto_approve_reads"]
    embed_model: str = DEFAULTS["embed_model"]
    qdrant_url: str = DEFAULTS["qdrant_url"]
    rag_collection: str = DEFAULTS["rag_collection"]
    rag_chunk_size: int = DEFAULTS["rag_chunk_size"]
    rag_chunk_overlap: int = DEFAULTS["rag_chunk_overlap"]
    working_dir: str = field(default_factory=lambda: os.getcwd())

    @classmethod
    def load(cls) -> Config:
        cfg = cls()
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except Exception as e:
                print(f"Warning: could not load config from {CONFIG_PATH}: {e}")
        cfg.qdrant_url = cls._resolve_qdrant_url(cfg.qdrant_url)
        return cfg

    @staticmethod
    def _resolve_qdrant_url(url: str) -> str:
        """Resolve relative qdrant paths to an absolute location in the user's data dir."""
        if url in (":memory:",) or url.startswith("http://") or url.startswith("https://"):
            return url
        p = Path(url)
        if not p.is_absolute():
            p = Path.home() / ".local" / "share" / "qwen-code" / p
        return str(p)

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v for k, v in self.__dict__.items() if k != "working_dir"}
        CONFIG_PATH.write_text(json.dumps(data, indent=2))
