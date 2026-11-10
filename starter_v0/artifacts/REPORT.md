# Day 03 Lab v2 Report — PETC Research Agent

## Team

- Team: PETC
- Members: Lê Hải Bắc (2A202603710), Vũ Đức Anh (2A202603714), Nguyễn Trọng Phương Bách (2A202603716)
- Provider/model: OpenRouter (`OPENROUTER_MODEL` or the project default)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

PETC Research Agent hỗ trợ nghiên cứu từ web, X/Twitter, arXiv và policy nội
bộ. Agent đọc URL được cung cấp, kiểm tra danh sách nguồn, rồi tạo digest
Markdown có link trích dẫn. Gửi Telegram luôn cần xác nhận rõ ràng trước.

**Link dùng thử (local):** `http://localhost:8501`

```powershell
streamlit run app.py
```

Để demo qua mạng, chạy `cloudflared tunnel --url http://localhost:8501` ở một
terminal khác và dán URL phiên đó tại đây. Không đưa API key vào report/link.

## A2. Tool agent có

| Tool | Làm được gì | Tool mới? |
|---|---|---|
| `clarify` | Hỏi dữ liệu còn thiếu hoặc xác nhận yes/no. | Không |
| `timeline` | Lấy bài gần đây của một tài khoản X/Twitter. | Không |
| `social_search` | Tìm thảo luận X/Twitter theo chủ đề. | Không |
| `lookup` | Tìm web hoặc tin tức theo thời gian. | Không |
| `fetch` | Đọc một URL cụ thể. | Không |
| `format` | Tạo digest Markdown từ item đã có. | Không |
| `source_check` | Kiểm tra URL lỗi/HTTP và phát hiện link trùng. | **Có** |
| `policy` | Tìm policy nội bộ. | Không |
| `papers` / `paper_text` | Tìm arXiv và trích text paper. | Không |
| `send` | Gửi Telegram sau xác nhận. | Không |

## A3. Câu hỏi mẫu để thử

1. `Tin AI hôm nay có gì nổi bật?`
2. `Lấy 3 tweet mới nhất của Elon Musk.`
3. `Tóm tắt https://openai.com/research/.`
4. `Kiểm tra https://openai.com/a, https://openai.com/a#intro và http://example.com trước khi làm digest.`
5. `Gửi bản tin này lên Telegram.`

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Before | After | Run File |
|---|---|---|---:|---:|---|
| v0 | starter baseline | Prompt starter khiến model đoán thiếu dữ liệu, gửi không xác nhận, và ép một tool. | — | 0.65 | `runs/v0_B_base_openrouter_20261110T110640701132.json` |
| v1 | `system_prompt.md`, routing/arg rules | Quy tắc routing rõ sẽ giảm sai args và bỏ sót `clarify`. | 0.65 | pending | Provider quota blocked valid run. |
| v2 | `system_prompt.md`, confirmation | Xác nhận yes/no sẽ chặn `send` sớm. | pending | pending | Provider quota blocked valid run. |
| v3 | multi-turn rules + `source_check` | Lượt mới nhất ghi đè context cũ; source validation có tool riêng. | pending | pending | Run after quota reset. |

Valid v0: 20 measured cases, 0 provider errors, `case_accuracy=0.65`,
`tool_routing_accuracy=0.80`, `argument_accuracy=0.65`,
`multiturn_accuracy=0.6667`. Parsed evidence: `analysis/baseline_v0.csv`.

**Provider blocker:** OpenRouter preflight returned `429 free-models-per-day`.
No v1/v2/v3 metric has been invented. After quota reset or selecting an
available provider/model, rerun each eval and replace pending cells with the
new run JSON metrics.

## B2. Failure Analysis (v0)

| Case | Failure | What failed | Fix |
|---|---|---|---|
| R03 | wrong arg | Query was `AI news today`, not core `AI`. | Separate query from `topic`/`timeframe`. |
| R10 | missing info | Guessed account and called `timeline`. | `clarify`, never guess a handle. |
| R11 | missing info | Searched without a supplied URL. | Ask for URL before `fetch`. |
| R12 | boundary | Called `send` before confirmation. | `clarify(response_type="yes_no")` first. |
| R13 | routing/args | Overloaded lookup and missed social search. | Permit parallel web + social tools. |
| M02 | wrong arg | Put time words in query. | Explicit timeframe mapping. |
| M05 | wrong arg | Retained limit 10 after user changed it to 3. | Newest turn wins. |

## B3. Team Eval Cases

`data/eval_group.json` now contains 10 cases: five single-turn (`G01`–`G05`)
and five multi-turn (`G06`–`G10`). They cover URL checking, policy/arXiv
routing, no-tool boundaries, clarification, corrections, source switching,
confirmed send, and paper text.

```powershell
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data\eval_group.json
```

## B4. Live Chat Evidence

`chat.py` writes to `transcripts/`. No fake transcript was created while the
provider returns HTTP 429. Once provider access is restored:

```powershell
python chat.py --provider openrouter --version v3
```

Run a news request, a missing-URL clarification followed by the URL, and a
Telegram request followed by explicit confirmation.

## B5. Implementation / Test Evidence

| Item | Evidence | Result |
|---|---|---|
| New tool | `tools/source_check/` | Validates URLs locally; normalizes fragments and identifies duplicates. |
| Registration | `tools/__init__.py`, `artifacts/tools.yaml` | Contract-compliant `source_check`. |
| Unit tests | `tests/test_tools_todo.py` | Three tool tests plus all starter TODO tests completed. |
| Offline verification | `python -m pytest -q` | **84 passed, 0 skipped**. |
| UI | `app.py`, `streamlit>=1.40.0` | Chat UI with provider/model selector and tool-event display. |

## B6. Reflection

- Prompt rules govern routing, confirmation, and multi-turn context.
- Tool descriptions communicate argument conventions and tool boundaries.
- Provider/quota failures must be recorded separately from model quality.
- Next: run v1–v3 and group eval on an available provider, then add the live
  transcript and public Tunnel URL.

## B7. Small Local Model Challenge

Not run: it needs Ollama and two local tool-calling models, neither assumed in
this workspace.
