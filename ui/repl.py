from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.rule import Rule

from agent.loop import AgentLoop
from config import Config

console = Console()

HISTORY_FILE = Path.home() / ".config" / "qwen-code" / "history"
BANNER = "[bold cyan]qwen-code[/bold cyan] [dim](qwen2.5-coder via Ollama)[/dim]"
HELP_TEXT = """\
[dim]Commands:  /exit  /quit  /clear  /model <name>  /wd <path>  /help[/dim]"""


def run_repl(config: Config) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        multiline=False,
    )
    agent = AgentLoop(config)

    console.print(Rule())
    console.print(BANNER)
    console.print(f"[dim]Working dir:[/dim] {config.working_dir}")
    console.print(f"[dim]Model:      [/dim] {config.model}")
    console.print(HELP_TEXT)
    console.print(Rule())

    while True:
        try:
            user_input = session.prompt("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye.[/dim]")
            break

        if not user_input:
            continue

        # Built-in slash commands
        if user_input.startswith("/"):
            if _handle_command(user_input, agent, config):
                continue
            else:
                break

        try:
            agent.run_once(user_input)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


def _handle_command(cmd: str, agent: AgentLoop, config: Config) -> bool:
    """Return True to continue, False to exit."""
    parts = cmd.split(maxsplit=1)
    name = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if name in ("/exit", "/quit"):
        console.print("[dim]Bye.[/dim]")
        return False
    elif name == "/clear":
        agent.ctx.messages = [agent.ctx.messages[0]]  # keep system prompt
        console.print("[dim]Context cleared.[/dim]")
    elif name == "/model":
        if arg:
            config.model = arg
            agent.llm.config.model = arg
            console.print(f"[dim]Model set to:[/dim] {arg}")
        else:
            console.print(f"[dim]Current model:[/dim] {config.model}")
    elif name == "/wd":
        if arg:
            import os
            p = Path(arg).expanduser().resolve()
            if p.is_dir():
                config.working_dir = str(p)
                os.chdir(p)
                console.print(f"[dim]Working dir set to:[/dim] {p}")
            else:
                console.print(f"[red]Not a directory:[/red] {arg}")
        else:
            console.print(f"[dim]Working dir:[/dim] {config.working_dir}")
    elif name == "/help":
        console.print(HELP_TEXT)
    else:
        console.print(f"[red]Unknown command:[/red] {name}")

    return True
