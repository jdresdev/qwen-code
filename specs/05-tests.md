# Spec 05 — Test Suite

## Problem
The project has zero tests. The most complex and failure-prone logic — the
fallback tool-call parser, context trimming, tool dispatch — is entirely
untested, making refactors and new features risky.

## Goal
Add a `pytest` test suite covering the three highest-risk modules. Tests must
run without Ollama or Qdrant running (all external I/O mocked).

## Test Modules

### `tests/test_tool_call_parser.py` — `llm/client._extract_tool_calls`
The parser handles multiple formats Qwen uses when it ignores the tools API.

| Case | Input | Expected |
|------|-------|----------|
| Bare JSON object | `{"name": "read_file", "arguments": {"path": "a.py"}}` | 1 tool call |
| Markdown code block | ` ```json\n{...}\n``` ` | 1 tool call |
| Array of tool calls | `[{...}, {...}]` | 2 tool calls |
| Mixed text + JSON | `Sure!\n{"name": "run_bash", ...}` | 1 tool call |
| `function` key alias | `{"function": "x", "parameters": {}}` | 1 tool call |
| Malformed JSON | `{"name": "x", "arguments":` | 0 tool calls |
| Empty string | `""` | 0 tool calls |
| Plain prose | `"I will help you."` | 0 tool calls |

### `tests/test_context_manager.py` — `agent/context.ContextManager`
| Case | Expected |
|------|----------|
| `add()` appends with correct role | message list grows |
| `get()` always starts with system prompt | first message is system |
| Trimming: total chars / 4 >= limit → oldest non-system messages dropped | length reduced |
| Trimming: always keeps at least last 4 messages | floor respected |
| `add_raw()` appends dict unchanged | dict in list |
| `clear()` resets to system prompt only | only system message remains |

### `tests/test_tool_executor.py` — `tools/executor.execute_tool`
Test dispatch and basic behaviour without real filesystem side effects where
possible. Use `tmp_path` (pytest fixture) for file operations.

| Case | Expected |
|------|----------|
| `read_file` on existing file | returns content |
| `read_file` on missing file | returns error string (no exception) |
| `write_file` creates file | file exists with correct content |
| `edit_file` single replace | file updated |
| `edit_file` string not found | returns error string |
| `glob_files` matching pattern | returns matching paths |
| `grep_files` pattern | returns matching lines |
| Unknown tool name | returns `"Unknown tool: ..."` error string |

## Acceptance Criteria
- [ ] `pytest` and `pytest-mock` added to `requirements.txt`.
- [ ] All test files in `tests/` directory.
- [ ] `tests/__init__.py` exists (empty).
- [ ] `pytest` passes with no external services running.
- [ ] No test imports trigger Ollama/Qdrant connections at collection time.
- [ ] Coverage of the listed cases for all three modules.

## Implementation Notes

### Mocking strategy
- `llm/client._extract_tool_calls` is a pure function — no mocks needed.
- `ContextManager` is pure Python — no mocks needed.
- `execute_tool` for RAG tools (`ingest_documents`, `retrieve_context`) should
  be skipped or mocked via `unittest.mock.patch` on the singleton initialisers.

### Running tests
```bash
pytest tests/ -v
```

### `conftest.py`
Add a `tmp_config` fixture that returns a `Config` with `working_dir` set to
`tmp_path`, used by executor tests.

## Files Touched
- `requirements.txt`
- `tests/__init__.py` (new)
- `tests/conftest.py` (new)
- `tests/test_tool_call_parser.py` (new)
- `tests/test_context_manager.py` (new)
- `tests/test_tool_executor.py` (new)
