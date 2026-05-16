from __future__ import annotations

import difflib
from pathlib import Path


def read_file(path: str, offset: int = 1, limit: int = 500, working_dir: str = ".") -> str:
    p = _resolve(path, working_dir)
    if not p.exists():
        return f"Error: file not found: {p}"
    if not p.is_file():
        return f"Error: not a file: {p}"
    try:
        lines = p.read_text(errors="replace").splitlines()
    except Exception as e:
        return f"Error reading file: {e}"

    start = max(0, offset - 1)
    end = start + limit
    chunk = lines[start:end]
    numbered = "\n".join(f"{start + i + 1}\t{line}" for i, line in enumerate(chunk))
    total = len(lines)
    header = f"File: {p}  ({total} lines total, showing {start+1}-{min(end, total)})\n"
    return header + numbered


def write_file(path: str, content: str, working_dir: str = ".") -> str:
    p = _resolve(path, working_dir)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {p}"
    except Exception as e:
        return f"Error writing file: {e}"


def edit_file(
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    working_dir: str = ".",
) -> str:
    p = _resolve(path, working_dir)
    if not p.exists():
        return f"Error: file not found: {p}"
    try:
        content = p.read_text(errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

    count = content.count(old_string)
    if count == 0:
        lines = content.splitlines()
        needle = old_string.splitlines()[0] if old_string else old_string
        close = difflib.get_close_matches(needle, lines, n=3, cutoff=0.6)
        hint = ("\nClose matches:\n" + "\n".join(f"  {l}" for l in close)) if close else ""
        return f"Error: old_string not found in file.{hint}"
    if count > 1 and not replace_all:
        positions = [
            i + 1
            for i, line in enumerate(content.splitlines())
            if old_string.splitlines()[0] in line
        ]
        return (
            f"Error: old_string appears {count} times (near lines {positions}). "
            "Provide more surrounding context to make it unique, or set replace_all=true."
        )

    new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
    try:
        p.write_text(new_content)
        replaced = count if replace_all else 1
        return f"Replaced {replaced} occurrence(s) in {p}."
    except Exception as e:
        return f"Error writing file: {e}"


def _resolve(path: str, working_dir: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = Path(working_dir) / p
    return p.resolve()
