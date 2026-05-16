from __future__ import annotations

import difflib
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# These tools are always approved silently
AUTO_APPROVE = {
    "read_file", "glob_files", "grep_files", "list_dir", "retrieve_context",
    "git_status", "git_diff", "git_log",
    "fetch_url",
    "get_symbol",
}

# Human-friendly descriptions of what each tool does
_DESCRIPTIONS = {
    "write_file": "Write file",
    "edit_file": "Edit file",
    "run_bash": "Run shell command",
    "ingest_documents": "Ingest documents into vector store",
    "git_commit": "Git commit",
    "replace_symbol": "Replace symbol",
}


def check_permission(tool_name: str, arguments_json: str) -> bool:
    """Return True if the tool call is allowed to proceed."""
    if tool_name in AUTO_APPROVE:
        return True

    try:
        args = json.loads(arguments_json) if arguments_json.strip() else {}
    except Exception:
        args = {}

    label = _DESCRIPTIONS.get(tool_name, tool_name)
    _show_permission_request(label, tool_name, args)

    try:
        answer = input("Allow? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Denied.[/yellow]")
        return False

    return answer in ("y", "yes")


def _make_diff(path: str, old_str: str, new_str: str, replace_all: bool) -> str:
    """Return a unified diff string for an edit_file preview, or '' on failure."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        original = p.read_text(errors="replace")
        modified = original.replace(old_str, new_str) if replace_all else original.replace(old_str, new_str, 1)
        lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=path,
            tofile=f"{path} (modified)",
            n=3,
        ))
        return "".join(lines)[:3000]
    except Exception:
        return ""


def _show_permission_request(label: str, tool_name: str, args: dict) -> None:
    if tool_name == "run_bash":
        body = args.get("command", "")
        desc = args.get("description", "")
        content = f"[bold]{desc}[/bold]\n\n" if desc else ""
        content += f"[yellow]$ {body}[/yellow]"
    elif tool_name == "write_file":
        path = args.get("path", "?")
        preview = (args.get("content", "") or "")[:500]
        content = f"[bold]Path:[/bold] {path}\n\n{preview}"
        if len(args.get("content", "")) > 500:
            content += "\n[dim]... (truncated)[/dim]"
    elif tool_name == "edit_file":
        path = args.get("path", "?")
        old_str = args.get("old_string", "")
        new_str = args.get("new_string", "")
        replace_all = args.get("replace_all", False)
        diff_text = _make_diff(path, old_str, new_str, replace_all)
        if diff_text:
            console.print(Panel(
                Syntax(diff_text, "diff", theme="ansi_dark"),
                title=f"[bold red]Permission required:[/bold red] {label}",
                border_style="red",
            ))
            return
        content = (
            f"[bold]Path:[/bold] {path}\n"
            f"[red]- {old_str[:200]}[/red]\n"
            f"[green]+ {new_str[:200]}[/green]"
        )
    elif tool_name == "replace_symbol":
        path = args.get("path", "?")
        name = args.get("name", "?")
        preview = (args.get("new_source", "") or "")[:300]
        content = f"[bold]File:[/bold] {path}\n[bold]Symbol:[/bold] {name}\n\n{preview}"
        if len(args.get("new_source", "")) > 300:
            content += "\n[dim]... (truncated)[/dim]"
    elif tool_name == "git_commit":
        msg = args.get("message", "")
        files = args.get("files")
        stage_all = args.get("all", False)
        content = f"[bold]Message:[/bold] {msg}"
        if files:
            content += "\n[bold]Files:[/bold] " + ", ".join(files)
        elif stage_all:
            content += "\n[bold]Staging:[/bold] all tracked modified files"
        else:
            content += "\n[bold]Staging:[/bold] already-staged changes"
    else:
        content = json.dumps(args, indent=2)[:500]

    console.print(Panel(content, title=f"[bold red]Permission required:[/bold red] {label}", border_style="red"))
