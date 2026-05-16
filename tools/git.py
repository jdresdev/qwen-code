from __future__ import annotations

import subprocess

GIT_DIFF_LIMIT = 8000  # chars


def _run(args: list[str], cwd: str) -> tuple[int, str]:
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def git_status(working_dir: str = ".") -> str:
    rc, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], working_dir)
    if rc != 0:
        return branch or "Error: not a git repository."
    _, status = _run(["git", "status", "--short"], working_dir)
    header = f"On branch {branch}\n"
    return header + (status if status else "(nothing to commit, working tree clean)")


def git_diff(
    path: str | None = None,
    staged: bool = False,
    commit: str | None = None,
    working_dir: str = ".",
) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    if commit:
        cmd.append(commit)
    if path:
        cmd += ["--", path]

    rc, output = _run(cmd, working_dir)
    if rc != 0:
        return output or "Error running git diff."
    if not output:
        return "(no diff)"
    if len(output) > GIT_DIFF_LIMIT:
        output = output[:GIT_DIFF_LIMIT] + f"\n\n[truncated — {len(output)} chars total]"
    return output


def git_log(
    n: int = 10,
    path: str | None = None,
    oneline: bool = True,
    working_dir: str = ".",
) -> str:
    cmd = ["git", "log", f"-{n}"]
    if oneline:
        cmd.append("--oneline")
    if path:
        cmd += ["--", path]

    rc, output = _run(cmd, working_dir)
    if rc != 0:
        return output or "Error running git log."
    return output if output else "(no commits)"


def git_commit(
    message: str,
    files: list[str] | None = None,
    stage_all: bool = False,
    working_dir: str = ".",
) -> str:
    # Stage files if requested
    if files:
        rc, out = _run(["git", "add", "--"] + files, working_dir)
        if rc != 0:
            return f"Error staging files: {out}"
    elif stage_all:
        rc, out = _run(["git", "add", "-u"], working_dir)
        if rc != 0:
            return f"Error staging files: {out}"

    rc, output = _run(["git", "commit", "-m", message], working_dir)
    if rc != 0:
        return f"Error: {output}"
    return output
