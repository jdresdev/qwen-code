# Spec 02 — Tool Retry Budget (max_tool_rounds)

## Problem
The agent loop has no upper bound on the number of tool-call rounds per user
message. A model stuck in a broken loop (e.g. repeatedly trying the same
failing `edit_file`) will spin indefinitely, burning tokens and blocking the UI.

## Goal
Add a configurable cap on how many tool-call rounds the agent may take for a
single user turn. When the cap is reached, print a warning and return control
to the REPL.

## Behaviour

### Happy path
1. Agent completes task in fewer rounds than the cap → no change.

### Cap hit
1. After `max_tool_rounds` rounds with at least one tool call each, the loop
   breaks.
2. A visible warning is printed:
   `[yellow]Warning: reached max tool rounds ({n}). Stopping.[/yellow]`
3. The conversation history up to that point is preserved.
4. The REPL prompt reappears normally.

### Edge cases
- Plain-text responses (no tool calls) do not count toward the cap.
- A round where all tools are denied counts toward the cap (it already breaks
  via the existing `all_denied` guard, so the cap just provides a secondary
  backstop).

## Acceptance Criteria
- [ ] `max_tool_rounds` config key added (default `10`).
- [ ] Loop breaks with warning message when cap is reached.
- [ ] Plain-text-only rounds do not increment the counter.
- [ ] Default documented in `CLAUDE.md` config table and `config.py`.
- [ ] Existing loop logic (all_denied guard, KeyboardInterrupt) unaffected.

## Implementation Notes

### `config.py`
Add field: `max_tool_rounds: int = 10`.

### `agent/loop.py`
Add a `rounds = 0` counter before the `while True:`. At the start of each
iteration that produces tool calls, increment `rounds`. After incrementing,
check `if rounds >= self.config.max_tool_rounds` and break with the warning.

### `~/.config/qwen-code/config.json` (user-facing)
Document the new key; no migration needed (default is backward-compatible).

## Files Touched
- `config.py`
- `agent/loop.py`
- `CLAUDE.md`
