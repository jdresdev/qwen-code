from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# These tools are always approved silently
AUTO_APPROVE = {"read_file", "glob_files", "grep_files", "list_dir", "retrieve_context"}

# Human-friendly descriptions of what each tool does
_DESCRIPTIONS = {
    "write_file": "Write file",
    "edit_file": "Edit file",
    "run_bash": "Run shell command",
    "ingest_documents": "Ingest documents into vector store",
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
        old = args.get("old_string", "")[:200]
        new = args.get("new_string", "")[:200]
        content = f"[bold]Path:[/bold] {path}\n[red]- {old}[/red]\n[green]+ {new}[/green]"
    else:
        content = json.dumps(args, indent=2)[:500]

    console.print(Panel(content, title=f"[bold red]Permission required:[/bold red] {label}", border_style="red"))
