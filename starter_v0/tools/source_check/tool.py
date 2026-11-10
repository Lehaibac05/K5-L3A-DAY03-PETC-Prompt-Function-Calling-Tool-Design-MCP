from __future__ import annotations

from collections import Counter
from typing import Any
from urllib.parse import urlparse

from tools._shared import err


def check_sources(urls: list[str] | None = None, require_https: bool = True) -> dict[str, Any]:
    """Validate, normalize, and deduplicate a small list of public source URLs."""
    try:
        if urls is None:
            urls = []
        if not isinstance(urls, list):
            raise ValueError("urls must be a list of URL strings")

        valid: list[dict[str, str]] = []
        invalid: list[dict[str, str]] = []
        normalized_urls: list[str] = []
        for raw_url in urls:
            if not isinstance(raw_url, str) or not raw_url.strip():
                invalid.append({"url": str(raw_url), "reason": "URL must be a non-empty string"})
                continue
            value = raw_url.strip()
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                invalid.append({"url": value, "reason": "URL must be an absolute http(s) URL"})
                continue
            if require_https and parsed.scheme != "https":
                invalid.append({"url": value, "reason": "HTTPS is required"})
                continue
            normalized = parsed._replace(fragment="").geturl()
            normalized_urls.append(normalized)
            valid.append({"url": value, "normalized_url": normalized, "domain": parsed.netloc.lower().removeprefix("www.")})

        counts = Counter(normalized_urls)
        duplicates = sorted(url for url, count in counts.items() if count > 1)
        unique = [item for item in valid if counts[item["normalized_url"]] == 1]
        return {
            "tool": "check_sources",
            "require_https": require_https,
            "valid": valid,
            "unique": unique,
            "invalid": invalid,
            "duplicates": duplicates,
            "summary": {"submitted": len(urls), "valid": len(valid), "invalid": len(invalid), "unique": len(unique)},
        }
    except Exception as exc:
        return err("check_sources", exc)
