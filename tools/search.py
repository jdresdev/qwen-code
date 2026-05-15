from __future__ import annotations

import re
import subprocess
import shutil
from pathlib import Path


MAX_RESULTS = 200


def glob_files(pattern: str, path: str | None = None, working_dir: str = ".") -> str:
    base = Path(path) if path else Path(working_dir)
    if not base.is_absolute():
        base = (Path(working_dir) / base).resolve()
    if not base.exists():
        return f"Error: directory not found: {base}"

    matches = sorted(base.rglob(pattern))
    if not matches:
        return f"No files found matching '{pattern}' in {base}"
    lines = [str(m.relative_to(base)) for m in matches[:MAX_RESULTS]]
    result = "\n".join(lines)
    if len(matches) > MAX_RESULTS:
        result += f"\n... [{len(matches) - MAX_RESULTS} more results truncated]"
    return result


def grep_files(
    pattern: str,
    path: str | None = None,
    glob: str | None = None,
    case_insensitive: bool = False,
    working_dir: str = ".",
) -> str:
    search_path = path if path else working_dir
    p = Path(search_path)
    if not p.is_absolute():
        p = (Path(working_dir) / p).resolve()

    # Prefer ripgrep if available
    if shutil.which("rg"):
        return _grep_rg(pattern, str(p), glob, case_insensitive)
    return _grep_python(pattern, p, glob, case_insensitive)


def _grep_rg(pattern: str, path: str, glob: str | None, case_insensitive: bool) -> str:
    cmd = ["rg", "--line-number", "--no-heading", pattern, path]
    if glob:
        cmd += ["--glob", glob]
    if case_insensitive:
        cmd.append("-i")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        if not output:
            return f"No matches for '{pattern}'"
        lines = output.splitlines()
        if len(lines) > MAX_RESULTS:
            output = "\n".join(lines[:MAX_RESULTS]) + f"\n... [{len(lines) - MAX_RESULTS} more]"
        return output
    except subprocess.TimeoutExpired:
        return "Error: grep timed out"
    except Exception as e:
        return f"Error running ripgrep: {e}"


def _grep_python(base: Path, pattern: str, glob_pat: str | None, case_insensitive: bool) -> str:
    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: invalid regex: {e}"

    file_pattern = glob_pat or "**/*"
    results: list[str] = []

    for file in sorted(base.rglob(file_pattern) if base.is_dir() else [base]):
        if not file.is_file():
            continue
        try:
            for i, line in enumerate(file.read_text(errors="replace").splitlines(), 1):
                if regex.search(line):
                    results.append(f"{file}:{i}:{line}")
                    if len(results) >= MAX_RESULTS:
                        results.append(f"... [truncated at {MAX_RESULTS} results]")
                        return "\n".join(results)
        except Exception:
            continue

    return "\n".join(results) if results else f"No matches for '{pattern}'"


def list_dir(path: str | None = None, working_dir: str = ".") -> str:
    base = Path(path) if path else Path(working_dir)
    if not base.is_absolute():
        base = (Path(working_dir) / base).resolve()
    if not base.exists():
        return f"Error: path not found: {base}"
    if not base.is_dir():
        return f"Error: not a directory: {base}"

    entries = sorted(base.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = []
    for e in entries:
        marker = "/" if e.is_dir() else ""
        lines.append(f"{e.name}{marker}")
    return "\n".join(lines) if lines else "(empty directory)"
