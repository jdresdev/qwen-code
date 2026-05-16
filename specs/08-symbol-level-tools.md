# Spec 08 — Symbol-Level Code Tools (tree-sitter)

## Problem
`read_file` + `edit_file` operate on raw text. For large files, the model must
read hundreds of lines to find one function, and string-replace edits are
fragile. Symbol-level tools let the agent operate on named functions, classes,
and methods directly — reducing context usage and edit failures.

## Goal
Add two tools backed by `tree-sitter`:
- `get_symbol` — extract the source of a named symbol.
- `replace_symbol` — replace the full body of a named symbol.

Initial language support: **Python** and **JavaScript/TypeScript**.

## Tools

### `get_symbol`
**Description:** Extract a named function, class, or method from a source file
using AST parsing.  
**Parameters:**
- `path` (string, required) — path to the source file.
- `name` (string, required) — symbol name (e.g. `"MyClass"`, `"parse_args"`,
  `"MyClass.my_method"`).

**Returns:** The full source text of the symbol (including decorators and
docstring), or an error string if not found.  
**Auto-approved:** yes (read-only).

### `replace_symbol`
**Description:** Replace the full source of a named function, class, or method
with new source text. The rest of the file is unchanged.  
**Parameters:**
- `path` (string, required) — path to the source file.
- `name` (string, required) — symbol name.
- `new_source` (string, required) — complete replacement source (including
  `def`/`class` line, decorators, docstring, body).

**Returns:** `"Replaced {name} in {path}."` or error string.  
**Requires user approval:** yes (write operation).

## Behaviour

### Symbol resolution
- Dot-notation (`"MyClass.my_method"`) resolves the method inside the class.
- For Python: uses `tree_sitter_languages` grammar; walks the AST for
  `function_definition` and `class_definition` nodes.
- For JS/TS: walks for `function_declaration`, `class_declaration`,
  `method_definition`.
- If multiple symbols share the same name, return/replace the **first** one
  and note the ambiguity in the return string.

### Unsupported language
If the file extension is not in the supported set, return:
`"Error: unsupported language for {ext}. Supported: .py, .js, .ts, .tsx, .jsx"`

### Line-number anchoring
`replace_symbol` records the byte range of the matched node, slices the file,
substitutes the new source, and writes back — preserving all surrounding code.

## Acceptance Criteria
- [ ] `tree-sitter` and `tree-sitter-languages` added to `requirements.txt`.
- [ ] `tools/symbols.py` implements `get_symbol` and `replace_symbol`.
- [ ] Both schemas in `tools/registry.py`.
- [ ] Dispatch in `tools/executor.py`.
- [ ] `get_symbol` in `AUTO_APPROVE`; `replace_symbol` requires confirmation.
- [ ] Dot-notation for method access works for Python and JS/TS.
- [ ] Unsupported extension returns a clear error string.
- [ ] Unit tests in `tests/test_symbols.py` cover: get function, get class,
      get method, replace function, symbol not found, unsupported extension.
- [ ] `CLAUDE.md` updated.

## Implementation Notes

### `tools/symbols.py`
```python
from tree_sitter_languages import get_parser

SUPPORTED = {".py": "python", ".js": "javascript", ".ts": "typescript",
             ".tsx": "tsx", ".jsx": "javascript"}

def _get_parser(path):
    ext = Path(path).suffix
    lang = SUPPORTED.get(ext)
    if not lang:
        return None, ext
    return get_parser(lang), ext

def get_symbol(path, name):
    parser, ext = _get_parser(path)
    if not parser:
        return f"Error: unsupported language for {ext}."
    source = Path(path).read_bytes()
    tree = parser.parse(source)
    node = _find_symbol(tree.root_node, name.split("."))
    if not node:
        return f"Error: symbol '{name}' not found in {path}."
    return source[node.start_byte:node.end_byte].decode()

def replace_symbol(path, name, new_source):
    parser, ext = _get_parser(path)
    if not parser:
        return f"Error: unsupported language for {ext}."
    source = Path(path).read_bytes()
    tree = parser.parse(source)
    node = _find_symbol(tree.root_node, name.split("."))
    if not node:
        return f"Error: symbol '{name}' not found in {path}."
    new_bytes = (source[:node.start_byte] +
                 new_source.encode() +
                 source[node.end_byte:])
    Path(path).write_bytes(new_bytes)
    return f"Replaced '{name}' in {path}."
```

### `_find_symbol` helper
Recursively walks the AST. For a single-part name, matches `function_definition`
/ `class_definition` nodes by their `name` child. For dot-notation, first
finds the class node then recurses into it for the method.

## Files Touched
- `tools/symbols.py` (new)
- `tools/registry.py`
- `tools/executor.py`
- `agent/permissions.py`
- `requirements.txt`
- `tests/test_symbols.py` (new)
- `CLAUDE.md`
