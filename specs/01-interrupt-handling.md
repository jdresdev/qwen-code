# Spec 01 — Interrupt Handling (Ctrl+C)

## Problem
The agent loop (`agent/loop.py`) has no graceful cancellation path. A mid-run
`run_bash` or slow LLM call cannot be stopped without killing the whole process,
leaving the terminal in a broken state.

## Goal
Allow the user to press Ctrl+C at any point during the agent loop and return
cleanly to the REPL prompt without corrupting conversation history or crashing.

## Behaviour

### Happy path
1. User sends a message; the agent loop starts.
2. User presses Ctrl+C at any point (during LLM call, spinner, tool execution).
3. The loop exits immediately with a short "Interrupted." notice.
4. The REPL prompt reappears; history is intact; the next message works normally.

### Edge cases
- Ctrl+C during a blocking `run_bash`: the subprocess must also be terminated
  (send SIGTERM to the child process group).
- Ctrl+C pressed twice in quick succession: same behaviour — no crash, no hang.
- Ctrl+C outside the loop (at the REPL idle prompt): existing prompt_toolkit
  behaviour; do not interfere.

## Acceptance Criteria
- [ ] `KeyboardInterrupt` caught inside `AgentLoop._loop()`.
- [ ] Any running subprocess in `tools/shell.py` is terminated on interrupt.
- [ ] A single-line cancellation message is printed to the console.
- [ ] The partial assistant message (if any) is **not** appended to context, so
      the next turn starts from a clean state.
- [ ] REPL returns to prompt without a Python traceback.
- [ ] Existing tests (once written) continue to pass.

## Implementation Notes

### `agent/loop.py`
Wrap the entire `while True:` body in a `try/except KeyboardInterrupt`. On
catch:
- Print `\n[yellow]Interrupted.[/yellow]` via Rich.
- `return` (do not re-add any partial message to context).

### `tools/shell.py`
`run_bash` spawns via `subprocess.Popen`. Pass `start_new_session=True` so the
child gets its own process group; on `KeyboardInterrupt` call
`os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` before re-raising.

### No new config keys required.

## Files Touched
- `agent/loop.py`
- `tools/shell.py`
