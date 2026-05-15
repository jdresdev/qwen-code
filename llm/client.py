from __future__ import annotations

import json
import re
import uuid
from typing import Generator, Any

from openai import OpenAI

from config import Config


class LLMClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(
            base_url=config.base_url,
            api_key="ollama",  # Ollama doesn't require a real key
        )

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> Generator[dict, None, None]:
        """Yields chunks as dicts:
          {"type": "text", "content": str}
          {"type": "tool_call", "id": str, "name": str, "arguments": str}
          {"type": "done"}

        Strategy:
          - With tools: non-streaming (structured tool_calls are unreliable in
            Qwen streaming mode via Ollama — they arrive as plain text JSON).
          - Without tools: streaming for real-time token output.
        """
        if tools:
            yield from self._chat_with_tools(messages, tools)
        else:
            yield from self._chat_stream(messages)

    # ------------------------------------------------------------------
    # Non-streaming path (used when tools are active)
    # ------------------------------------------------------------------

    def _chat_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> Generator[dict, None, None]:
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=False,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            # Structured tool calls (ideal path)
            if msg.content:
                yield {"type": "text", "content": msg.content}
            for tc in msg.tool_calls:
                yield {
                    "type": "tool_call",
                    "id": tc.id or str(uuid.uuid4()),
                    "name": tc.function.name,
                    "arguments": tc.function.arguments or "{}",
                }
        elif msg.content:
            # Fallback: Qwen may output tool calls as plain-text JSON
            parsed = _extract_tool_calls(msg.content)
            if parsed:
                for tc in parsed:
                    yield tc
            else:
                yield {"type": "text", "content": msg.content}

        yield {"type": "done"}

    # ------------------------------------------------------------------
    # Streaming path (used for plain conversation, no tools)
    # ------------------------------------------------------------------

    def _chat_stream(self, messages: list[dict]) -> Generator[dict, None, None]:  # noqa: E301
        stream = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield {"type": "text", "content": delta.content}

        yield {"type": "done"}


# ------------------------------------------------------------------
# Text-based tool call parser (fallback for models that ignore the
# tools API and output JSON as plain text content instead)
# ------------------------------------------------------------------

def _extract_tool_calls(text: str) -> list[dict]:
    """
    Try to parse one or more tool calls from a plain-text model response.

    Handles formats Qwen commonly uses:
      1. Bare JSON object:    {"name": "x", "arguments": {...}}
      2. Markdown code block: ```json\n{"name": ...}\n```
      3. Array of the above:  [{"name": ...}, ...]
    """
    text = text.strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to pull the first {...} block from mixed text
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return []
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return []

    items = data if isinstance(data, list) else [data]

    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("function")
        args = item.get("arguments") or item.get("parameters") or {}
        if not name:
            continue
        results.append({
            "type": "tool_call",
            "id": str(uuid.uuid4()),
            "name": name,
            "arguments": json.dumps(args) if isinstance(args, dict) else str(args),
        })
    return results
