"""Tests for llm.client._extract_tool_calls — the fallback plain-text parser."""

import json

from llm.client import _extract_tool_calls


def test_bare_json_object():
    text = json.dumps({"name": "read_file", "arguments": {"path": "a.py"}})
    result = _extract_tool_calls(text)
    assert len(result) == 1
    assert result[0]["name"] == "read_file"
    assert result[0]["type"] == "tool_call"
    assert "id" in result[0]


def test_markdown_code_block():
    text = '```json\n{"name": "run_bash", "arguments": {"command": "ls"}}\n```'
    result = _extract_tool_calls(text)
    assert len(result) == 1
    assert result[0]["name"] == "run_bash"


def test_markdown_code_block_no_language_tag():
    text = '```\n{"name": "list_dir", "arguments": {}}\n```'
    result = _extract_tool_calls(text)
    assert len(result) == 1
    assert result[0]["name"] == "list_dir"


def test_array_of_tool_calls():
    items = [
        {"name": "read_file", "arguments": {"path": "a.py"}},
        {"name": "write_file", "arguments": {"path": "b.py", "content": "hi"}},
    ]
    result = _extract_tool_calls(json.dumps(items))
    assert len(result) == 2
    assert result[0]["name"] == "read_file"
    assert result[1]["name"] == "write_file"


def test_mixed_text_before_json():
    payload = json.dumps({"name": "run_bash", "arguments": {"command": "ls -la"}})
    text = f"Sure! I'll run that for you.\n{payload}"
    result = _extract_tool_calls(text)
    assert len(result) == 1
    assert result[0]["name"] == "run_bash"


def test_function_key_alias():
    text = json.dumps({"function": "list_dir", "parameters": {"path": "."}})
    result = _extract_tool_calls(text)
    assert len(result) == 1
    assert result[0]["name"] == "list_dir"


def test_malformed_json_returns_empty():
    result = _extract_tool_calls('{"name": "x", "arguments":')
    assert result == []


def test_empty_string_returns_empty():
    result = _extract_tool_calls("")
    assert result == []


def test_plain_prose_returns_empty():
    result = _extract_tool_calls("I will help you with that task right away!")
    assert result == []


def test_arguments_preserved_as_json_string():
    args = {"path": "foo.py", "offset": 5, "limit": 100}
    text = json.dumps({"name": "read_file", "arguments": args})
    result = _extract_tool_calls(text)
    assert json.loads(result[0]["arguments"]) == args


def test_missing_name_skipped():
    items = [
        {"arguments": {"path": "a.py"}},           # no name — should be skipped
        {"name": "glob_files", "arguments": {}},
    ]
    result = _extract_tool_calls(json.dumps(items))
    assert len(result) == 1
    assert result[0]["name"] == "glob_files"


def test_each_call_gets_unique_id():
    items = [
        {"name": "read_file", "arguments": {"path": "a.py"}},
        {"name": "read_file", "arguments": {"path": "b.py"}},
    ]
    result = _extract_tool_calls(json.dumps(items))
    assert result[0]["id"] != result[1]["id"]
