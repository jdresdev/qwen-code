"""Tests for tools.executor.execute_tool dispatch and error handling."""

import json

import pytest

from tools.executor import execute_tool


def jdump(d: dict) -> str:
    return json.dumps(d)


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

def test_read_file_existing(tmp_config, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("line one\nline two\n")
    result = execute_tool("read_file", jdump({"path": str(f)}), tmp_config)
    assert "line one" in result
    assert "line two" in result


def test_read_file_missing_returns_error(tmp_config, tmp_path):
    result = execute_tool("read_file", jdump({"path": str(tmp_path / "ghost.txt")}), tmp_config)
    assert "Error" in result


def test_read_file_with_offset_and_limit(tmp_config, tmp_path):
    f = tmp_path / "many.txt"
    f.write_text("\n".join(f"line {i}" for i in range(1, 21)))
    result = execute_tool("read_file", jdump({"path": str(f), "offset": 5, "limit": 3}), tmp_config)
    assert "line 5" in result
    assert "line 7" in result
    assert "line 8" not in result


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

def test_write_file_creates_file(tmp_config, tmp_path):
    target = tmp_path / "out.txt"
    result = execute_tool("write_file", jdump({"path": str(target), "content": "hello world"}), tmp_config)
    assert target.exists()
    assert target.read_text() == "hello world"
    assert "Written" in result


def test_write_file_creates_parent_dirs(tmp_config, tmp_path):
    target = tmp_path / "sub" / "dir" / "file.txt"
    execute_tool("write_file", jdump({"path": str(target), "content": "data"}), tmp_config)
    assert target.exists()


# ---------------------------------------------------------------------------
# edit_file
# ---------------------------------------------------------------------------

def test_edit_file_single_replace(tmp_config, tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\ny = 2\n")
    result = execute_tool(
        "edit_file",
        jdump({"path": str(f), "old_string": "x = 1", "new_string": "x = 99"}),
        tmp_config,
    )
    assert "Replaced" in result
    assert "x = 99" in f.read_text()
    assert "y = 2" in f.read_text()  # surrounding content unchanged


def test_edit_file_replace_all(tmp_config, tmp_path):
    f = tmp_path / "code.py"
    f.write_text("a = 0\na = 0\na = 0\n")
    result = execute_tool(
        "edit_file",
        jdump({"path": str(f), "old_string": "a = 0", "new_string": "a = 1", "replace_all": True}),
        tmp_config,
    )
    assert "3" in result  # 3 occurrences replaced
    assert f.read_text() == "a = 1\na = 1\na = 1\n"


def test_edit_file_not_found_returns_error(tmp_config, tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\n")
    result = execute_tool(
        "edit_file",
        jdump({"path": str(f), "old_string": "z = 99", "new_string": "z = 0"}),
        tmp_config,
    )
    assert "Error" in result


def test_edit_file_multiple_occurrences_without_replace_all_returns_error(tmp_config, tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\nx = 1\n")
    result = execute_tool(
        "edit_file",
        jdump({"path": str(f), "old_string": "x = 1", "new_string": "x = 2"}),
        tmp_config,
    )
    assert "Error" in result


# ---------------------------------------------------------------------------
# glob_files
# ---------------------------------------------------------------------------

def test_glob_files_matches_pattern(tmp_config, tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    (tmp_path / "c.txt").write_text("")
    result = execute_tool("glob_files", jdump({"pattern": "**/*.py", "path": str(tmp_path)}), tmp_config)
    assert "a.py" in result
    assert "b.py" in result
    assert "c.txt" not in result


# ---------------------------------------------------------------------------
# grep_files
# ---------------------------------------------------------------------------

def test_grep_files_finds_matches(tmp_config, tmp_path):
    f = tmp_path / "src.py"
    f.write_text("def hello():\n    pass\n\ndef world():\n    pass\n")
    result = execute_tool(
        "grep_files",
        jdump({"pattern": "def hello", "path": str(tmp_path)}),
        tmp_config,
    )
    assert "hello" in result
    assert "world" not in result


def test_grep_files_case_insensitive(tmp_config, tmp_path):
    f = tmp_path / "readme.md"
    f.write_text("Hello World\n")
    result = execute_tool(
        "grep_files",
        jdump({"pattern": "hello", "path": str(tmp_path), "case_insensitive": True}),
        tmp_config,
    )
    assert "Hello" in result


# ---------------------------------------------------------------------------
# unknown tool
# ---------------------------------------------------------------------------

def test_unknown_tool_returns_error_string(tmp_config):
    result = execute_tool("does_not_exist", "{}", tmp_config)
    assert "does_not_exist" in result
