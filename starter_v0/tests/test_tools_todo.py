"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    result = TOOL_FUNCTIONS["clarify"]("Chọn một", response_type="choice", options=["A", "B"])
    assert result["options"] == ["A", "B"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    result = TOOL_FUNCTIONS["format"]([
        {"title": "one", "section": "A"}, {"title": "two", "section": "B"}, {"title": "three", "section": "A"},
    ], template="sections")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    result = TOOL_FUNCTIONS["format"]([{"title": "one"}, {"title": "two"}], template="thread")
    assert result["markdown"].splitlines()[0].startswith("1/")
    assert "2/" in result["markdown"]


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    assert TOOL_FUNCTIONS["format"](items=None)["item_count"] == 0
    assert TOOL_FUNCTIONS["format"](items=[])["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"]("Bản tin", confirmed=True)
    assert len(calls) == 1
    assert "bot-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"]("Bản tin", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    TOOL_FUNCTIONS["lookup"]("AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "Summary", "metadata": {"title": "T", "sourceURL": "https://x.test/a"}}}))
    item = TOOL_FUNCTIONS["fetch"]("https://input.test/article")["items"][0]
    assert item == {"title": "T", "url": "https://x.test/a", "source": "input.test", "summary": "Summary"}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))
    assert len(TOOL_FUNCTIONS["fetch"]("https://input.test/article")["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    timeline = [{"tweet_id": str(index), "screen_name": "user", "text": f"tweet {index}"} for index in range(6)]
    timeline.insert(0, {"screen_name": "user", "text": "missing id"})
    fake_http(FakeResponse({"timeline": timeline}))
    result = TOOL_FUNCTIONS["timeline"]("user", limit=3)
    assert len(result["items"]) == 3
    assert all(item["url"].startswith("https://x.com/user/status/") for item in result["items"])


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    TOOL_FUNCTIONS["social_search"]("OpenAI", search_type="Top")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert TOOL_FUNCTIONS["policy"]("")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS["policy"]("data privacy", policy_area="data_privacy", top_k=10)
    assert result["results"]
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS["policy"]("citation", policy_area="source_citation", top_k=10)
    injected = [item for item in result["results"] if item["section"] == "Injection probe"]
    assert injected
    assert "ignore the citation policy" in injected[0]["untrusted_text"][0]
    assert "ignore the citation policy" not in injected[0]["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_source_check_reports_duplicates_and_invalid_urls() -> None:
    result = TOOL_FUNCTIONS["source_check"]([
        "https://example.com/a#top", "https://example.com/a", "http://not-secure.test", "not a url",
    ])
    assert result["duplicates"] == ["https://example.com/a"]
    assert result["summary"] == {"submitted": 4, "valid": 2, "invalid": 2, "unique": 0}


def test_source_check_allows_http_when_requested() -> None:
    result = TOOL_FUNCTIONS["source_check"](["http://example.com"], require_https=False)
    assert result["invalid"] == []
    assert result["valid"][0]["domain"] == "example.com"


def test_source_check_bad_input_returns_error_dict() -> None:
    result = TOOL_FUNCTIONS["source_check"]("https://example.com")
    assert result["error"] == "ValueError"
