from __future__ import annotations

import subprocess


MAX_OUTPUT = 10_000  # chars


def run_bash(command: str, description: str = "", timeout: int = 30, working_dir: str = ".") -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
        )
        output = result.stdout + result.stderr
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n... [truncated, {len(output)} chars total]"
        if not output:
            output = f"(exit code {result.returncode}, no output)"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"
