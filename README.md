# qwen-code

A local AI coding assistant CLI — a Claude Code-style tool powered by **Qwen2.5-Coder** running via **Ollama**. It implements an agentic loop with tool use (file ops, bash, search, RAG), a terminal REPL, and a permission system for dangerous operations.

RAG stack: **nomic-embed-text** (via Ollama) for embeddings + **Qdrant** for vector storage.

---

## Prerequisites

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
# Set qdrant_url to a relative path in config — resolved under ~/.local/share/qwen-code/

# Option C — in-memory (no persistence)
# Set qdrant_url: ":memory:" in config
```

---

## Usage

**Interactive REPL:**
```bash
python main.py
```

**One-shot mode:**
```bash
python main.py "read main.py and explain it"
python main.py --model qwen2.5-coder:32b --wd /path/to/project "list files"
python main.py --base-url http://localhost:11434/v1
```

**REPL slash commands:**

| Command | Effect |
|---|---|
| `/model <name>` | Switch model mid-session |
| `/wd <path>` | Change working directory |
| `/clear` | Reset conversation (keeps system prompt) |
| `/help` | Show all commands |
| `/exit` or `/quit` | Exit |

---

## Configuration

Optional config file at `~/.config/qwen-code/config.json`. All keys and their defaults:

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

---

## Architecture

```
main.py            Entry point — parses CLI args, delegates to REPL or one-shot AgentLoop
config.py          Config dataclass, loads from ~/.config/qwen-code/config.json

llm/
  client.py        OpenAI-compatible client → Ollama at localhost:11434/v1
                   With tools: non-streaming (Qwen's tool calls break under streaming)
                   Without tools: streaming for real-time token output
                   Fallback parser handles Qwen emitting tool calls as plain-text JSON

tools/
  registry.py      TOOL_SCHEMAS — OpenAI function-calling JSON schemas for all tools
  executor.py      Dispatches tool name → implementation; always returns a string
                   RAG singletons lazily initialised on first RAG tool use
  file_ops.py      read_file, write_file, edit_file
  shell.py         run_bash (subprocess, 30s timeout, 10k char output cap)
  search.py        glob_files (pathlib.rglob), grep_files (ripgrep or Python re), list_dir

rag/
  embedder.py      Calls Ollama /v1/embeddings — nomic-embed-text, 768-dim vectors
  vector_store.py  Qdrant wrapper: ensure_collection, upsert, search, delete_by_source
  ingestion.py     ingest()  — chunk by word count → batch embed → upsert (idempotent)
                   retrieve() — embed query → top-k search → format for LLM

agent/
  context.py       Holds messages[], system prompt; trims oldest when near token limit
  permissions.py   Auto-approves read-only tools; prompts y/N for write/destructive ones
  loop.py          Core reasoning loop: user msg → LLM → tool calls → results → repeat

ui/
  repl.py          prompt_toolkit REPL with persistent history and rich formatting
```

### Permission system

- **Auto-approved** (read-only): `read_file`, `glob_files`, `grep_files`, `list_dir`, `retrieve_context`
- **Requires `y/N` prompt**: `write_file`, `edit_file`, `run_bash`, `ingest_documents`

A formatted preview of the action (command, diff, or content) is shown before asking.

### Tool loop

For each user message, `AgentLoop`:
1. Sends messages + tool schemas to the LLM
2. Collects text and tool calls from the response
3. For each tool call: checks permission → executes → appends result to context
4. Loops back to step 1 until the model returns a plain text response with no tool calls
5. Breaks early if the user denies every tool call in a round (prevents infinite loops)

---

## Adding a New Tool

1. Add the Python implementation in `tools/` (or to an existing file).
2. Add its JSON schema to `TOOL_SCHEMAS` in `tools/registry.py`.
3. Add the dispatch case in `tools/executor.py`.
4. If it's a write/destructive operation, add it to `agent/permissions.py`.
