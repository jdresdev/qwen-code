from __future__ import annotations

from pathlib import Path

SUPPORTED = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

_CLASS_TYPES = frozenset({"class_definition", "class_declaration"})
_BODY_TYPES = frozenset({"block", "class_body"})
_TOP_TYPES = frozenset({
    "function_definition", "function_declaration",
    "class_definition", "class_declaration",
    "decorated_definition",
})
_METHOD_TYPES = frozenset({
    "function_definition", "method_definition", "decorated_definition",
})


def _get_parser(path: str):
    """Return (Parser, ext) or (None, ext) if the language is unsupported."""
    ext = Path(path).suffix.lower()
    lang_name = SUPPORTED.get(ext)
    if not lang_name:
        return None, ext
    try:
        from tree_sitter import Language, Parser
        if lang_name == "python":
            import tree_sitter_python as m
            lang = Language(m.language())
        elif lang_name == "javascript":
            import tree_sitter_javascript as m
            lang = Language(m.language())
        elif lang_name == "typescript":
            import tree_sitter_typescript as m
            lang = Language(m.language_typescript())
        elif lang_name == "tsx":
            import tree_sitter_typescript as m
            lang = Language(m.language_tsx())
        else:
            return None, ext
        return Parser(lang), ext
    except ImportError:
        return None, ext


def _symbol_name(node) -> str | None:
    """Return the identifier name of a symbol node, unwrapping decorated_definition."""
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type in _TOP_TYPES - {"decorated_definition"}:
                name_node = child.child_by_field_name("name")
                return name_node.text.decode() if name_node else None
        return None
    name_node = node.child_by_field_name("name")
    return name_node.text.decode() if name_node else None


def _unwrap(node):
    """Unwrap a decorated_definition to its inner definition node."""
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type in _TOP_TYPES - {"decorated_definition"}:
                return child
    return node


def _find_top_level(root, name: str):
    for child in root.children:
        if child.type in _TOP_TYPES and _symbol_name(child) == name:
            return child
    return None


def _find_method(class_node, method_name: str):
    for child in class_node.children:
        if child.type in _BODY_TYPES:
            for item in child.children:
                if item.type in _METHOD_TYPES and _symbol_name(item) == method_name:
                    return item
    return None


def _find_symbol(root, name_parts: list[str]):
    if len(name_parts) == 1:
        return _find_top_level(root, name_parts[0])
    if len(name_parts) == 2:
        sym = _find_top_level(root, name_parts[0])
        if not sym:
            return None
        class_node = _unwrap(sym)
        if class_node.type not in _CLASS_TYPES:
            return None
        return _find_method(class_node, name_parts[1])
    return None


def get_symbol(path: str, name: str) -> str:
    """Extract the full source of a named function, class, or method."""
    parser, ext = _get_parser(path)
    if not parser:
        supported = ", ".join(sorted(SUPPORTED))
        return f"Error: unsupported extension '{ext}'. Supported: {supported}."
    try:
        source = Path(path).read_bytes()
    except Exception as e:
        return f"Error reading file: {e}"

    tree = parser.parse(source)
    node = _find_symbol(tree.root_node, name.split("."))
    if not node:
        return f"Error: symbol '{name}' not found in {path}."
    return source[node.start_byte:node.end_byte].decode(errors="replace")


def replace_symbol(path: str, name: str, new_source: str) -> str:
    """Replace the full source of a named symbol with new_source."""
    parser, ext = _get_parser(path)
    if not parser:
        supported = ", ".join(sorted(SUPPORTED))
        return f"Error: unsupported extension '{ext}'. Supported: {supported}."
    try:
        source = Path(path).read_bytes()
    except Exception as e:
        return f"Error reading file: {e}"

    tree = parser.parse(source)
    node = _find_symbol(tree.root_node, name.split("."))
    if not node:
        return f"Error: symbol '{name}' not found in {path}."

    new_bytes = source[:node.start_byte] + new_source.encode() + source[node.end_byte:]
    try:
        Path(path).write_bytes(new_bytes)
    except Exception as e:
        return f"Error writing file: {e}"
    return f"Replaced '{name}' in {path}."
