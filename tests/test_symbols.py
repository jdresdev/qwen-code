"""Tests for tools.symbols — get_symbol and replace_symbol."""

import pytest
from tools.symbols import get_symbol, replace_symbol

SAMPLE_PY = '''\
def hello():
    return "hello"


def world():
    return "world"


class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"

    def farewell(self, name):
        return f"Goodbye, {name}!"
'''

SAMPLE_JS = '''\
function hello() {
  return "hello";
}

class Greeter {
  greet(name) {
    return `Hello, ${name}!`;
  }
}
'''


# ---------------------------------------------------------------------------
# Python symbols
# ---------------------------------------------------------------------------

def test_get_top_level_function(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    result = get_symbol(str(f), "hello")
    assert "def hello" in result
    assert 'return "hello"' in result
    assert "world" not in result


def test_get_top_level_class(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    result = get_symbol(str(f), "Greeter")
    assert "class Greeter" in result
    assert "greet" in result
    assert "farewell" in result


def test_get_method_dot_notation(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    result = get_symbol(str(f), "Greeter.greet")
    assert "def greet" in result
    assert "Hello" in result
    assert "farewell" not in result


def test_get_symbol_not_found(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    result = get_symbol(str(f), "nonexistent")
    assert "Error" in result
    assert "nonexistent" in result


def test_replace_function(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    new_body = 'def hello():\n    return "replaced"'
    result = replace_symbol(str(f), "hello", new_body)
    assert "Replaced" in result
    content = f.read_text()
    assert "replaced" in content
    assert "world" in content          # surrounding code unchanged
    assert "class Greeter" in content  # surrounding code unchanged


def test_replace_method(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    new_body = "    def greet(self, name):\n        return 'hi'"
    result = replace_symbol(str(f), "Greeter.greet", new_body)
    assert "Replaced" in result
    content = f.read_text()
    assert "hi" in content
    assert "farewell" in content  # other method untouched


def test_replace_symbol_not_found(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(SAMPLE_PY)
    result = replace_symbol(str(f), "ghost", "def ghost(): pass")
    assert "Error" in result


# ---------------------------------------------------------------------------
# JavaScript symbols
# ---------------------------------------------------------------------------

def test_get_js_function(tmp_path):
    f = tmp_path / "mod.js"
    f.write_text(SAMPLE_JS)
    result = get_symbol(str(f), "hello")
    assert "function hello" in result
    assert "Greeter" not in result


def test_get_js_method(tmp_path):
    f = tmp_path / "mod.js"
    f.write_text(SAMPLE_JS)
    result = get_symbol(str(f), "Greeter.greet")
    assert "greet" in result
    assert "Hello" in result


# ---------------------------------------------------------------------------
# Unsupported extension
# ---------------------------------------------------------------------------

def test_unsupported_extension(tmp_path):
    f = tmp_path / "mod.rb"
    f.write_text("def foo; end\n")
    result = get_symbol(str(f), "foo")
    assert "Error" in result
    assert "unsupported" in result.lower()
