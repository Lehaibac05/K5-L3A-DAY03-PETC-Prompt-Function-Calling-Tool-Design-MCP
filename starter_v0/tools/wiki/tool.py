from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

UA = {"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"}


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    """Return the lead summary of a Wikipedia article. Never raises: errors come back as a dict."""
    title = str(title or "").strip()
    if not title:
        return {"tool": "wiki", "error": "ValueError", "message": "title is empty"}
    if lang not in {"en", "vi"}:
        lang = "en"
    try:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
        response = requests.get(url, headers=UA, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wiki", "status": "not_found", "title": title}
        response.raise_for_status()
        data = response.json()
        return {
            "tool": "wiki",
            "status": "ok",
            "title": data.get("title", title),
            "summary": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as exc:
        return err("wiki", exc)