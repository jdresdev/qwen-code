# Spec 04 — Git Tools

## Problem
The agent has no awareness of version control. It cannot check what changed,
stage files, or commit — limiting its usefulness for real development workflows.

## Goal
Add four git tools: `git_status`, `git_diff`, `git_log`, and `git_commit`.
Read-only tools are auto-approved; `git_commit` requires user confirmation.

## Tools

### `git_status`
**Description:** Show the working tree status (staged, unstaged, untracked files).  
**Parameters:** `path` (string, optional) — repo root, defaults to working dir.  
**Returns:** Output of `git status --short` plus branch name.  
**Auto-approved:** yes.

### `git_diff`
**Description:** Show changes between commits, or working tree vs HEAD.  
**Parameters:**
- `path` (string, optional) — file or directory to scope diff.
- `staged` (boolean, optional, default false) — diff staged changes (`--cached`).
- `commit` (string, optional) — diff against a specific commit/ref.  

**Returns:** Unified diff output (truncated to 8000 chars with a notice if longer).  
**Auto-approved:** yes.

### `git_log`
**Description:** Show recent commit history.  
**Parameters:**
- `n` (integer, optional, default 10) — number of commits.
- `path` (string, optional) — limit to commits touching this path.
- `oneline` (boolean, optional, default true) — compact format.  

**Returns:** Formatted log output.  
**Auto-approved:** yes.

### `git_commit`
**Description:** Stage specified files and create a commit.  
**Parameters:**
- `message` (string, required) — commit message.
- `files` (array of strings, optional) — files to stage; omit to use already-staged files.
- `all` (boolean, optional, default false) — stage all tracked modified files (`-a`).  

**Returns:** Commit hash and summary line on success, error string on failure.  
**Requires user approval:** yes (treated like `run_bash`).

## Acceptance Criteria
- [ ] All four tools implemented in `tools/git.py`.
- [ ] Schemas added to `tools/registry.py`.
- [ ] Dispatch cases added to `tools/executor.py`.
- [ ] `git_status`, `git_diff`, `git_log` added to `AUTO_APPROVE` set in
      `agent/permissions.py`.
- [ ] `git_commit` prompts for confirmation (shown in the permission system).
- [ ] `git_diff` output truncated at 8000 chars with a trailing notice.
- [ ] All tools return an informative error string if not inside a git repo.
- [ ] `CLAUDE.md` updated with the four new tools.

## Implementation Notes

### `tools/git.py`
Each function shells out via `subprocess.run` with `cwd=working_dir` (taken
from `Config.working_dir`). Use `capture_output=True, text=True`.

No dependency on `gitpython` — raw subprocess keeps the dep footprint small.

### Error handling
If `git` is not installed or the directory is not a repo, return the stderr
string (e.g. `"fatal: not a git repository"`).

## Files Touched
- `tools/git.py` (new)
- `tools/registry.py`
- `tools/executor.py`
- `agent/permissions.py`
- `CLAUDE.md`
