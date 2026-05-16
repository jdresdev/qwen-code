from __future__ import annotations

SYSTEM_PROMPT = """\
You are qwen-code, a local AI coding assistant running on-device. You help users with software \
engineering tasks: reading and writing code, running commands, searching files, and \
explaining concepts. You have access to tools for file operations and shell execution.

Guidelines:
- Think step by step. Use tools to explore before making changes.
- Always read a file before editing it.
- Prefer targeted edits (edit_file) over full rewrites (write_file) for existing files.
- Show your reasoning briefly before calling tools.
- When running bash commands, use descriptive `description` values.
"""


class ContextManager:
    def __init__(self, limit: int = 28_000) -> None:
        self.limit = limit
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def add(self, role: str, content: str, **kwargs) -> None:
        msg: dict = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)
        self._maybe_trim()

    def add_raw(self, message: dict) -> None:
        self.messages.append(message)
        self._maybe_trim()

    def get(self) -> list[dict]:
        return self.messages

    def clear(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def token_estimate(self) -> int:
        # Rough estimate: 1 token ≈ 4 chars
        return len(str(self.messages)) // 4

    def _maybe_trim(self) -> None:
        if self.token_estimate() < self.limit:
            return
        # Remove oldest non-system messages until under limit
        # Keep at least the last 4 messages for continuity
        i = 1
        while self.token_estimate() >= self.limit and i < len(self.messages) - 4:
            if self.messages[i]["role"] != "system":
                self.messages.pop(i)
            else:
                i += 1
