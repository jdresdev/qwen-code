# Spec 07 — Web Fetch Tool

## Problem
The agent cannot look up documentation, read GitHub issues, or fetch any
external resource. This forces the user to copy-paste content manually for any
task that requires referencing the web.

## Goal
Add a `fetch_url` tool that fetches a URL, converts it to clean plain text,
and returns it to the agent — enabling doc lookups, issue reading, and
general web research within the coding workflow.

## Tool Definition

### `fetch_url`
**Description:** Fetch a URL and return its content as plain text. HTML pages
are converted to readable markdown. Binary content is rejected.  
**Parameters:**
- `url` (string, required) — Full URL (must start with `http://` or `https://`).
- `max_chars` (integer, optional, default 8000) — Truncate output to this many
  characters. Appends a notice if truncated.

**Returns:** Plain text / markdown of the page content, or an error string.  
**Auto-approved:** yes (read-only, no side effects).

## Behaviour

### Happy path
1. Agent calls `fetch_url(url="https://docs.python.org/3/library/pathlib.html")`.
2. Tool fetches the page with a 15 s timeout.
3. HTML is converted to markdown via `html2text`.
4. Result is truncated to `max_chars` if needed.
5. Agent receives the text and uses it to answer.

### Error cases
| Condition | Return value |
|-----------|-------------|
| Non-http/https scheme | `"Error: only http/https URLs are supported."` |
| HTTP error (4xx/5xx) | `"Error: HTTP {status} for {url}"` |
| Timeout | `"Error: request timed out after 15s."` |
| Non-text content type | `"Error: content type {ct} is not text."` |
| Network error | `"Error: {exception message}"` |

### Security
- Only `http` and `https` schemes allowed (no `file://`, `ftp://`, etc.).
- Redirect limit: follow up to 5 redirects, then return error.
- No cookies or session state maintained between calls.

## Acceptance Criteria
- [ ] `fetch_url` implemented in `tools/web.py`.
- [ ] Schema added to `tools/registry.py`.
- [ ] Dispatch added to `tools/executor.py`.
- [ ] Added to `AUTO_APPROVE` in `agent/permissions.py`.
- [ ] `httpx` and `html2text` added to `requirements.txt`.
- [ ] URL scheme validation rejects non-http/https.
- [ ] Truncation appends `"\n\n[truncated at {max_chars} chars]"`.
- [ ] All error conditions return strings (never raise to the agent).
- [ ] `CLAUDE.md` updated.

## Implementation Notes

### `tools/web.py`
```python
import httpx
import html2text

def fetch_url(url: str, max_chars: int = 8000) -> str:
    if not url.startswith(("http://", "https://")):
        return "Error: only http/https URLs are supported."
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True, max_redirects=5)
        r.raise_for_status()
    except httpx.TimeoutException:
        return "Error: request timed out after 15s."
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:
        return f"Error: {e}"

    ct = r.headers.get("content-type", "")
    if "text" not in ct and "json" not in ct:
        return f"Error: content type {ct} is not text."

    if "html" in ct:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        text = h.handle(r.text)
    else:
        text = r.text

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[truncated at {max_chars} chars]"
    return text
```

## Files Touched
- `tools/web.py` (new)
- `tools/registry.py`
- `tools/executor.py`
- `agent/permissions.py`
- `requirements.txt`
- `CLAUDE.md`
