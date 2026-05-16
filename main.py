#!/usr/bin/env python3
"""qwen-code — a local coding assistant powered by Qwen via Ollama."""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

from rich.console import Console

from config import Config
from agent.loop import AgentLoop
from ui.repl import run_repl

_console = Console()


def _start_auto_index(config: Config) -> None:
    """Kick off background indexing of config.working_dir. Never raises."""
    def _run() -> None:
        try:
            from rag.ingestion import auto_ingest
            result = auto_ingest(config.working_dir, config)
            _console.print(f"[dim]{result}[/dim]")
        except Exception as e:
            _console.print(f"[dim yellow]auto-index warning: {e}[/dim yellow]")

    threading.Thread(target=_run, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local AI coding assistant using Qwen via Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # interactive REPL
  python main.py "list files here"        # one-shot prompt
  python main.py --model qwen2.5-coder:32b
  python main.py --wd /path/to/project
        """,
    )
    parser.add_argument("prompt", nargs="?", help="One-shot prompt (skips REPL)")
    parser.add_argument("--model", help="Override model name (default: qwen2.5-coder:7b)")
    parser.add_argument("--wd", "--working-dir", dest="working_dir", help="Set working directory")
    parser.add_argument("--base-url", help="Ollama API base URL (default: http://localhost:11434/v1)")
    parser.add_argument("--no-index", action="store_true", help="Skip auto-indexing the working directory")
    args = parser.parse_args()

    config = Config.load()

    if args.model:
        config.model = args.model
    if args.working_dir:
        wd = Path(args.working_dir).expanduser().resolve()
        if not wd.is_dir():
            print(f"Error: not a directory: {wd}", file=sys.stderr)
            sys.exit(1)
        config.working_dir = str(wd)
    if args.base_url:
        config.base_url = args.base_url

    if config.auto_index and not args.no_index:
        _start_auto_index(config)

    if args.prompt:
        # One-shot mode
        agent = AgentLoop(config)
        agent.run_once(args.prompt)
    else:
        # Interactive REPL
        run_repl(config)


if __name__ == "__main__":
    main()
