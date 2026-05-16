# Spec 03 — Diff-based `edit_file` with replace_all

## Problem
The current `edit_file` tool does an exact single-occurrence string replace.
It fails when:
- The model hallucinates a slight whitespace difference.
- The target string appears more than once and the model doesn't know which
  occurrence to replace.

## Goal
Make `edit_file` more robust by:
1. Adding a `replace_all` flag for intentional multi-occurrence replacements.
2. Showing a unified diff preview (in the permission prompt) so the user can
   see what will change before approving.
3. Returning a clear, actionable error when the string is not found (include
   a similarity hint).

## Behaviour

### replace_all = false (default, current behaviour)
- Fails if `old_string` not found → error message with the 3 most similar
  lines in the file (using `difflib.get_close_matches`).
- Fails if `old_string` found more than once → error message listing line
  numbers of all occurrences, and suggests using `replace_all: true`.

### replace_all = true
- Replaces every occurrence of `old_string` with `new_string`.
- Returns how many replacements were made.

### Permission prompt (write operations)
- When `auto_approve_reads` is false (or for `edit_file` specifically, which
  always requires approval), show a unified diff before the y/N prompt:
  ```
  --- path/to/file
  +++ path/to/file (modified)
  @@ -10,4 +10,4 @@
  -old line
  +new line
  ```

## Acceptance Criteria
- [ ] `replace_all` parameter added to `edit_file` schema in `registry.py`.
- [ ] `file_ops.py` handles `replace_all=True` (replace all) and
      `replace_all=False` (error on 0 or 2+ occurrences).
- [ ] Error on not-found includes similarity hint via `difflib`.
- [ ] Error on multiple occurrences lists line numbers.
- [ ] Unified diff shown in terminal before user approves `edit_file`.
- [ ] Unit tests cover: single replace, replace_all, not-found, multi-found.

## Implementation Notes

### `tools/file_ops.py` — `edit_file`
```python
import difflib

def edit_file(path, old_string, new_string, replace_all=False):
    content = Path(path).read_text()
    count = content.count(old_string)
    if count == 0:
        # similarity hint
        lines = content.splitlines()
        close = difflib.get_close_matches(old_string.splitlines()[0], lines, n=3)
        return f"String not found. Close matches:\n" + "\n".join(close)
    if count > 1 and not replace_all:
        positions = [i+1 for i,l in enumerate(content.splitlines())
                     if old_string.splitlines()[0] in l]
        return f"Found {count} occurrences at lines {positions}. Use replace_all=true."
    new_content = content.replace(old_string, new_string)
    Path(path).write_text(new_content)
    replaced = count if replace_all else 1
    return f"Replaced {replaced} occurrence(s)."
```

### `tools/registry.py`
Add `replace_all: boolean` (optional, default false) to `edit_file` schema.

### `agent/permissions.py`
Before the y/N prompt for `edit_file`, generate and print a unified diff using
`difflib.unified_diff`.

## Files Touched
- `tools/file_ops.py`
- `tools/registry.py`
- `agent/permissions.py`
