# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A local AI coding assistant CLI — a Claude Code-style tool powered by **Qwen2.5-Coder** running via **Ollama**. It implements an agentic loop with tool use (file ops, bash, search, RAG), a terminal REPL, and a permission system for dangerous operations.

RAG stack: **nomic-embed-text** (via Ollama) for embeddings + **Qdrant** for vector storage.

## Running and Development

**Prerequisites:**
```bash
pip install -r requirements.txt
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text      # required for RAG
```

**Qdrant** (pick one):
```bash
# Option A — Docker server (default config points here)
docker run -p 6333:6333 qdrant/qdrant

# Option B — local file storage (no server needed)
# Set qdrant_url: "~/.local/share/qwen-code/qdrant_data" in config
# Relative paths are resolved under ~/.local/share/qwen-code/

# Option C — in-memory (no persistence)
# Set qdrant_url: ":memory:" in config
```

**Start the REPL:**
```bash
python main.py
```

**One-shot mode:**
```bash
python main.py "read main.py and explain it"
python main.py --model qwen2.5-coder:32b --wd /path/to/project "list files"
python main.py --base-url http://localhost:11434/v1  # override Ollama endpoint
```

**Override settings at runtime via REPL commands:**
```
/model qwen2.5-coder:32b
/wd /path/to/project
/clear      # reset conversation history
/help       # show all slash commands
/exit
```

**Config file** (optional, overrides defaults): `~/.config/qwen-code/config.json`

All config keys and their defaults:

| Key | Default | Purpose |
|---|---|---|
| `model` | `qwen2.5-coder:7b` | Ollama model |
| `base_url` | `http://localhost:11434/v1` | Ollama API endpoint |
| `temperature` | `0.1` | Sampling temperature |
| `max_tokens` | `8192` | Max tokens per response |
| `context_limit` | `28000` | Token count before trimming history |
| `bash_timeout` | `30` | Shell command timeout (seconds) |
| `auto_approve_reads` | `true` | Skip prompts for read-only tools |
| `embed_model` | `nomic-embed-text` | Ollama embedding model |
| `qdrant_url` | `http://localhost:6333` | Qdrant location |
| `rag_collection` | `default` | Qdrant collection name |
| `rag_chunk_size` | `500` | Words per chunk during ingestion |
| `rag_chunk_overlap` | `50` | Overlapping words between chunks |
| `max_tool_rounds` | `10` | Max tool-call rounds per user turn before stopping |

## Architecture

```
main.py            Entry point — parses CLI args, delegates to REPL or one-shot AgentLoop
config.py          Config dataclass, loads from ~/.config/qwen-code/config.json

llm/
  client.py        OpenAI-compatible client → Ollama at localhost:11434/v1
                   With tools: non-streaming (Qwen's tool calls break under streaming)
                   Without tools: streaming for real-time token output
                   Fallback parser _extract_tool_calls() handles Qwen emitting tool
                   calls as plain-text JSON instead of using the tools API

tools/
  registry.py      TOOL_SCHEMAS list — OpenAI function-calling JSON schemas for all tools
  executor.py      Dispatches tool_call.name → implementation, always returns a string
                   RAG singletons (embedder, store) lazily initialised on first RAG tool use
  file_ops.py      read_file, write_file, edit_file
  shell.py         run_bash (subprocess, 30s timeout, 10k char output cap)
  search.py        glob_files (pathlib.rglob), grep_files (ripgrep or Python re), list_dir
  git.py           git_status, git_diff, git_log (auto-approved), git_commit (requires confirmation)

rag/
  embedder.py      Embedder — calls Ollama /v1/embeddings (nomic-embed-text, 768-dim)
  vector_store.py  VectorStore — Qdrant wrapper: ensure_collection, upsert, search, delete_by_source
  ingestion.py     ingest() — load files → chunk by word count → batch embed (32/batch) → upsert
                   retrieve() — embed query → search → format top-k chunks for LLM

agent/
  context.py       ContextManager — holds messages[], system prompt, trims oldest when near limit
  permissions.py   AUTO_APPROVE = {read_file, glob_files, grep_files, list_dir, retrieve_context,
                                   git_status, git_diff, git_log}
                   Prompts y/N for: write_file, edit_file, run_bash, ingest_documents, git_commit
  loop.py          AgentLoop.run_once() — the core reasoning loop:
                     1. Add user msg → 2. Stream LLM → 3. If tool_calls: check perm → execute
                     → append tool result → repeat from 2. Stop when plain text response.
                     Breaks early if user denies all tool calls in a round (prevents infinite loop)

ui/
  repl.py          prompt_toolkit REPL with input history (~/.config/qwen-code/history),
                   rich formatting, slash commands
```

## Key Design Decisions

- **Ollama via OpenAI SDK**: `openai` package pointed at `http://localhost:11434/v1`, `api_key="ollama"`. No real API key needed.
- **Non-streaming with tools**: When tools are provided, the LLM call uses `stream=False`. Qwen's tool calls are unreliable in streaming mode via Ollama — they arrive as plain text JSON rather than structured tool_calls. The fallback parser `_extract_tool_calls` in `llm/client.py` handles this, supporting bare JSON objects, markdown code blocks, and arrays.
- **Tool executor never raises**: All exceptions in `executor.py` are caught and returned as error strings so the agent can self-correct.
- **Permission system**: Only `write_file`, `edit_file`, `run_bash`, and `ingest_documents` require user approval. `retrieve_context` is auto-approved (read-only).
- **Context trimming**: Oldest non-system messages are dropped when `len(str(messages)) / 4 >= context_limit`, always keeping at least the last 4 messages.
- **Lazy RAG init**: `_embedder` and `_store` in `executor.py` are `None` at startup and only instantiated the first time a RAG tool is called. This keeps startup fast when RAG isn't needed.
- **Idempotent ingestion**: `ingest()` calls `delete_by_source()` before upserting, so re-indexing a file replaces old chunks rather than duplicating them.
- **Qdrant URL resolution**: Relative paths in `qdrant_url` are resolved under `~/.local/share/qwen-code/`. `:memory:` and `http(s)://` URLs pass through unchanged.

## Adding a New Tool

1. Add the Python implementation in `tools/` (or to an existing file).
2. Add its JSON schema to `TOOL_SCHEMAS` in `tools/registry.py`.
3. Add the dispatch case in `tools/executor.py`.
4. If it's a write/destructive operation, add it to the prompt logic in `agent/permissions.py`.
