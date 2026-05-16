from __future__ import annotations

import os
import signal
import subprocess


MAX_OUTPUT = 10_000  # chars


def run_bash(command: str, description: str = "", timeout: int = 30, working_dir: str = ".") -> str:
    proc = None
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(proc)
            return f"Error: command timed out after {timeout}s"
        output = stdout + stderr
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n... [truncated, {len(output)} chars total]"
        if not output:
            output = f"(exit code {proc.returncode}, no output)"
        return output
    except KeyboardInterrupt:
        if proc is not None:
            _kill(proc)
        raise
    except Exception as e:
        return f"Error running command: {e}"


def _kill(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()
    except Exception:
        pass
