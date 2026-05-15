# Architecture Overview

A local AI coding assistant CLI powered by **Qwen2.5-Coder** via **Ollama**. Implements an agentic loop with tool use (file ops, bash, search, RAG), a terminal REPL, and a permission system for dangerous operations.

---

## Entry Point

**`main.py`**
Parses CLI args and decides between two modes:
- **One-shot**: `python main.py "your prompt"` — runs the agent once and exits
- **Interactive REPL**: `python main.py` — starts the terminal loop

CLI flags let you override model, working directory, and base URL at startup.

---

## Configuration — `config.py`

A dataclass that holds all runtime settings. Loaded once at startup from `~/.config/qwen-code/config.json`, with hardcoded defaults as fallback.

| Setting | Default | Purpose |
|---|---|---|
| `model` | `qwen2.5-coder:7b` | Which Ollama model to use |
| `base_url` | `http://localhost:11434/v1` | Ollama API endpoint |
| `qdrant_url` | `http://localhost:6333` | Where Qdrant lives |
| `rag_collection` | `default` | Qdrant collection name |
| `context_limit` | 28 000 tokens | When to start trimming history |
| `bash_timeout` | 30s | Max time for shell commands |

---

## LLM Layer — `llm/client.py`

Wraps the OpenAI SDK pointed at Ollama. Has two paths:

- **With tools** → non-streaming. Qwen's tool calls are unreliable when streamed, so it waits for the full response. Includes a fallback parser (`_extract_tool_calls`) that handles Qwen outputting tool calls as raw JSON text instead of using the tools API properly.
- **Without tools** → streaming. Tokens are printed to the terminal as they arrive.

Yields normalized chunks: `{"type": "text"|"tool_call"|"done", ...}`

---

## Agent Layer

### `agent/context.py` — ContextManager

Holds the conversation history as a list of messages, starting with a system prompt that sets the assistant's behavior. When the estimated token count exceeds the limit, it drops the oldest non-system messages, always keeping at least the last 4 for continuity.

### `agent/permissions.py` — Permission System

Gates which tools require user approval:

- **Auto-approved** (read-only, safe): `read_file`, `glob_files`, `grep_files`, `list_dir`, `retrieve_context`
- **Requires `y/N` prompt**: `write_file`, `edit_file`, `run_bash`, `ingest_documents`

Shows a formatted preview of what the tool will do before asking — the bash command, the file diff, or the content to write.

### `agent/loop.py` — AgentLoop

The core reasoning loop. For each user message:

1. Sends messages + tool schemas to the LLM
2. Collects text and tool calls from the response
3. For each tool call: checks permission → executes → appends result to context
4. Loops back to step 1 until the model returns a plain text response with no tool calls
5. Breaks early if the user denies every tool call in a round (prevents infinite loops)

---

## Tools Layer

### `tools/registry.py`
A list of OpenAI function-calling JSON schemas — this is what gets sent to the LLM so it knows what tools exist and what arguments they take.

### `tools/executor.py`
Dispatches by tool name to the actual implementations. Never raises — all exceptions are caught and returned as error strings so the agent can self-correct. RAG singletons (`_embedder`, `_store`) are initialized lazily here on first use.

### Tool Implementations

| File | Tools |
|---|---|
| `tools/file_ops.py` | `read_file`, `write_file`, `edit_file` |
| `tools/shell.py` | `run_bash` (subprocess, 30s timeout, 10k char cap) |
| `tools/search.py` | `glob_files`, `grep_files` (ripgrep or Python fallback), `list_dir` |

---

## RAG Layer

### `rag/embedder.py` — Embedder
Calls Ollama's `/v1/embeddings` endpoint with `nomic-embed-text` to turn text into 768-dimensional vectors. Has both single (`embed`) and batch (`embed_batch`) methods.

### `rag/vector_store.py` — VectorStore
Qdrant wrapper. Handles three modes via `qdrant_url`: in-memory, local file, or HTTP server. Core operations: `ensure_collection`, `upsert`, `search`, `delete_by_source`.

### `rag/ingestion.py`
- `ingest()`: walks a file/directory, reads text files, chunks them by word count with overlap, embeds in batches of 32, upserts to Qdrant. Idempotent — deletes old chunks for a file before re-inserting.
- `retrieve()`: embeds a query, searches Qdrant top-k, formats results for the LLM.

---

## UI — `ui/repl.py`

A `prompt_toolkit` REPL with persistent input history (`~/.config/qwen-code/history`). Uses `rich` throughout for markdown rendering, spinners, colored panels, and permission prompts.

### Slash Commands

| Command | Effect |
|---|---|
| `/model <name>` | Switch model mid-session |
| `/wd <path>` | Change working directory |
| `/clear` | Reset conversation (keeps system prompt) |
| `/exit` or `/quit` | Exit |
| `/help` | Show commands |
