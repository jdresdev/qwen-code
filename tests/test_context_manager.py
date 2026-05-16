"""Tests for agent.context.ContextManager."""

from agent.context import ContextManager, SYSTEM_PROMPT


def test_add_appends_with_correct_role():
    ctx = ContextManager()
    ctx.add("user", "hello")
    assert ctx.messages[-1] == {"role": "user", "content": "hello"}


def test_add_extra_kwargs_included():
    ctx = ContextManager()
    ctx.add("assistant", "hi", name="qwen")
    assert ctx.messages[-1]["name"] == "qwen"


def test_get_always_starts_with_system():
    ctx = ContextManager()
    ctx.add("user", "one")
    ctx.add("assistant", "two")
    messages = ctx.get()
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT


def test_add_raw_appends_unchanged():
    ctx = ContextManager()
    raw = {"role": "tool", "tool_call_id": "abc123", "content": "result"}
    ctx.add_raw(raw)
    assert ctx.messages[-1] is raw


def test_clear_resets_to_system_only():
    ctx = ContextManager()
    ctx.add("user", "hello")
    ctx.add("assistant", "hi there")
    ctx.clear()
    assert len(ctx.messages) == 1
    assert ctx.messages[0]["role"] == "system"
    assert ctx.messages[0]["content"] == SYSTEM_PROMPT


def test_trimming_removes_oldest_non_system():
    # limit=5 tokens → threshold ~20 chars; long messages will force trimming
    ctx = ContextManager(limit=5)
    for i in range(15):
        ctx.add("user", f"message number {i} with extra padding to push over limit")
    # System message must still be first
    assert ctx.messages[0]["role"] == "system"
    # Must have trimmed — not all 16 messages present
    assert len(ctx.messages) < 16


def test_trimming_preserves_system_message():
    ctx = ContextManager(limit=5)
    for i in range(20):
        ctx.add("user", f"msg {i} " * 20)
    assert ctx.messages[0]["role"] == "system"
    assert ctx.messages[0]["content"] == SYSTEM_PROMPT


def test_trimming_keeps_at_least_last_4_messages():
    # The guard is i < len(messages) - 4, so at least 4 non-system messages survive
    ctx = ContextManager(limit=1)  # always over the limit
    for i in range(10):
        ctx.add("user", f"msg {i}")
    # system + at least 4 user messages must remain
    assert len(ctx.messages) >= 5


def test_token_estimate_reflects_content():
    ctx = ContextManager()
    before = ctx.token_estimate()
    ctx.add("user", "x" * 400)  # adds ~100 tokens worth of chars
    after = ctx.token_estimate()
    assert after > before
