# Spec 06 — Auto-Ingest Working Directory on Startup

## Problem
RAG is opt-in: the user must manually call `ingest_documents` before the agent
can do semantic search over the codebase. This means RAG is never used unless
the user explicitly asks — defeating its purpose for coding tasks.

## Goal
Automatically index the working directory at startup (or when `--wd` changes
in the REPL), so `retrieve_context` works out of the box without any manual
step.

## Behaviour

### Startup (one-shot and REPL modes)
1. After config is loaded and working directory is resolved, scan `--wd` for
   indexable files.
2. Run ingestion in a **background thread** so startup latency is hidden.
3. Print a one-line notice once indexing completes:
   `[dim]Indexed N files into RAG.[/dim]`
4. If Qdrant is unreachable, print a warning and continue — auto-index failure
   must never block startup.

### `/wd <path>` REPL command
Re-index the new working directory the same way (background thread, completion
notice).

### `--no-index` CLI flag
Skip auto-indexing entirely. Useful when the user manages ingestion manually
or when the working directory is very large.

### File filter
Index files matching these extensions by default:
`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`, `.java`, `.c`, `.cpp`,
`.h`, `.md`, `.txt`, `.yaml`, `.yml`, `.toml`, `.json`

Exclude:
- Hidden directories (`.git`, `.venv`, `node_modules`, `__pycache__`, `.mypy_cache`)
- Files larger than 500 KB
- Binary files (detected by trying UTF-8 decode)

### Config key
`auto_index: true` — set to `false` to disable without using the CLI flag.

## Acceptance Criteria
- [ ] `auto_index` config key added (default `true`).
- [ ] `--no-index` CLI flag added to `main.py` argument parser.
- [ ] Indexing runs in a `threading.Thread`; startup is not blocked.
- [ ] Completion notice printed after indexing finishes.
- [ ] Qdrant failure caught and logged as a warning; startup continues.
- [ ] File filter excludes hidden dirs and large/binary files.
- [ ] `/wd` command triggers re-indexing of the new directory.
- [ ] `CLAUDE.md` updated with the new config key and CLI flag.

## Implementation Notes

### `rag/ingestion.py`
Add `auto_ingest(directory, config)` — filters files and calls existing
`ingest()` for each, batched for efficiency.

### `main.py`
After resolving config, if `config.auto_index` and not `--no-index`:
```python
import threading
t = threading.Thread(target=auto_ingest, args=(config.working_dir, config), daemon=True)
t.start()
```

### `ui/repl.py`
In the `/wd` handler, after updating `config.working_dir`, start the same
background thread.

## Files Touched
- `config.py`
- `main.py`
- `rag/ingestion.py`
- `ui/repl.py`
- `CLAUDE.md`
