from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from agent.context import ContextManager
from agent.permissions import check_permission
from config import Config
from llm.client import LLMClient
from tools.executor import execute_tool
from tools.registry import TOOL_SCHEMAS

console = Console()


class AgentLoop:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.ctx = ContextManager(limit=config.context_limit)
        self.llm = LLMClient(config)

    def run_once(self, user_input: str) -> None:
        """Process a single user message through the full agentic loop."""
        self.ctx.add("user", user_input)
        self._loop()

    def _loop(self) -> None:
        rounds = 0
        while True:
            snapshot = len(self.ctx.messages)
            try:
                done, used_tools = self._step()
            except KeyboardInterrupt:
                del self.ctx.messages[snapshot:]
                console.print("\n[yellow]Interrupted.[/yellow]")
                return
            if used_tools:
                rounds += 1
                if rounds >= self.config.max_tool_rounds:
                    console.print(
                        f"\n[yellow]Warning: reached max tool rounds "
                        f"({self.config.max_tool_rounds}). Stopping.[/yellow]"
                    )
                    break
            if done:
                break

    def _step(self) -> tuple[bool, bool]:
        """One reasoning round: LLM call → optional tool execution.
        Returns (done, used_tools): done=True means stop the loop;
        used_tools=True means at least one tool call was executed this round."""
        # Collect the full streamed response
        text_parts: list[str] = []
        tool_calls: list[dict] = []

        with Live(Spinner("dots", text="Thinking…"), console=console, refresh_per_second=10):
            for chunk in self.llm.chat(self.ctx.get(), tools=TOOL_SCHEMAS):
                if chunk["type"] == "text":
                    text_parts.append(chunk["content"])
                elif chunk["type"] == "tool_call":
                    tool_calls.append(chunk)
                elif chunk["type"] == "done":
                    break

        full_text = "".join(text_parts).strip()

        # Build the assistant message for history
        assistant_msg: dict = {"role": "assistant", "content": full_text or None}
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in tool_calls
            ]
        self.ctx.add_raw(assistant_msg)

        # Print any text the model produced
        if full_text:
            console.print(Markdown(full_text))

        # If no tool calls, the model is done — exit the loop
        if not tool_calls:
            return True, False

        # Execute each tool call
        all_denied = True
        for tc in tool_calls:
            name = tc["name"]
            args_json = tc["arguments"]

            # Show what tool is being called
            console.print(
                Panel(
                    Text(f"{name}({_summarize_args(args_json)})", style="cyan"),
                    title="[bold blue]Tool call[/bold blue]",
                    border_style="blue",
                    expand=False,
                )
            )

            # Check permission
            if not check_permission(name, args_json):
                result = "Tool call denied by user."
            else:
                all_denied = False
                result = execute_tool(name, args_json, self.config)

            # Print result preview
            preview = result[:300] + ("…" if len(result) > 300 else "")
            console.print(f"[dim]{preview}[/dim]\n")

            # Add tool result to context
            self.ctx.add_raw({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        # If every tool was denied, stop to avoid infinite loop
        if all_denied:
            return True, False

        return False, True


def _summarize_args(args_json: str, max_len: int = 80) -> str:
    """Return a compact single-line summary of tool arguments."""
    import json
    try:
        args = json.loads(args_json)
        parts = []
        for k, v in args.items():
            v_str = str(v).replace("\n", "↵")
            if len(v_str) > 40:
                v_str = v_str[:37] + "..."
            parts.append(f"{k}={v_str!r}")
        summary = ", ".join(parts)
        return summary[:max_len]
    except Exception:
        return args_json[:max_len]
