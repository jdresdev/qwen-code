from __future__ import annotations

import httpx
import html2text as _html2text


def fetch_url(url: str, max_chars: int = 8000) -> str:
    """Fetch a URL and return its content as plain text / markdown.
    HTML is converted via html2text. Output is capped at max_chars."""
    if not url.startswith(("http://", "https://")):
        return "Error: only http/https URLs are supported."

    try:
        with httpx.Client(max_redirects=5) as client:
            response = client.get(url, timeout=15, follow_redirects=True)
        response.raise_for_status()
    except httpx.TimeoutException:
        return "Error: request timed out after 15s."
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except httpx.TooManyRedirects:
        return "Error: too many redirects."
    except Exception as e:
        return f"Error: {e}"

    content_type = response.headers.get("content-type", "")
    if "text" not in content_type and "json" not in content_type:
        return f"Error: content type '{content_type}' is not text."

    if "html" in content_type:
        converter = _html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.body_width = 0  # no line wrapping
        text = converter.handle(response.text)
    else:
        text = response.text

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[truncated at {max_chars} chars]"
    return text
