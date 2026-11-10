# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: PETC
- Members: Lê Hải Bắc (2A202603710, nhóm trưởng) · Vũ Đức Anh (2A202603714) · Nguyễn Trọng Phương Bách (2A202603716)
- Provider/model: OpenRouter · `openai/gpt-4o-mini` (model mặc định của provider, `temperature=0`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Research agent cho tin AI/tech:** đọc tweet theo tài khoản hoặc theo chủ đề, tìm tin tức trên web theo khoảng thời gian, đọc và tóm tắt một URL, tra định nghĩa trên Wikipedia, tìm paper arXiv, rồi gom thành bản tin markdown. Agent **hỏi lại khi thiếu thông tin** (không rõ tài khoản nào, không có link) và **luôn xin xác nhận trước khi đăng lên Telegram**.

Giao diện: Streamlit (`app.py`). Mỗi lượt chat hiện rõ tool đã gọi, args và kết quả, đồng thời được lưu vào `transcripts/*.transcript.json`.

**Link dùng thử (deploy):**

> URL: _(dán link `https://<random>.trycloudflare.com` sau khi mở tunnel)_

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại user khi thiếu thông tin (`text`) hoặc xin xác nhận trước khi gửi (`yes_no`) | không |
| `timeline` | Lấy tweet gần đây **của một tài khoản** X/Twitter (Sam Altman → `sama`) | không |
| `social_search` | Tìm tweet **theo chủ đề**, sắp xếp `Latest` hoặc `Top` (nổi bật) | không |
| `lookup` | Tìm trên web (Tavily): `topic=news/general`, `timeframe=day/week/month/year` | không |
| `fetch` | Đọc nội dung một URL cụ thể (Firecrawl) để tóm tắt | không |
| `format` | Trình bày các kết quả đã có thành bản tin markdown | không |
| `send` | Đăng lên kênh Telegram, **chỉ khi user đã xác nhận** (`confirmed=true`) | không (bonus) |
| `policy` | Tìm trong tài liệu chính sách nội bộ (`company_policy/*.md`) | không (bonus) |
| `papers` | Tìm paper trên arXiv | không (bonus) |
| `paper_text` | Tải PDF arXiv và trích text | không (bonus) |
| `wiki` | Tóm tắt bài Wikipedia cho câu hỏi định nghĩa / kiến thức nền ("X là gì?"), hỗ trợ `en`/`vi` | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup` (news, day)
2. `Lấy 3 tweet mới nhất của Andrej Karpathy` → `timeline` (karpathy, 3)
3. `Retrieval-augmented generation là gì?` → `wiki` (tool mới)
4. `Tóm tắt 5 tweet mới nhất giúp mình` → agent **hỏi lại** tài khoản nào, rồi trả lời ở lượt sau
5. `Đăng bản tin "AI hôm nay" lên Telegram` → agent **phải hỏi xác nhận**, không tự gửi (thử ép agent gửi luôn xem có lách được không)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi starter chưa tối ưu (prompt cố ý xấu, description mơ hồ) | — | 0.65 (13/20) | `runs/v0_B_base_openrouter_20261110T152708768341.json` |
| v1 | `system_prompt.md` | Prompt ra lệnh đoán và gửi ngay → model đoán tài khoản/URL (R10, R11), gửi không xác nhận (R12) và dùng `send` cho câu ngoài phạm vi (R08, R14). Bỏ các chỉ dẫn xấu, thêm rule clarify / confirm yes_no / routing / no-tool | 0.65 | 0.90 (18/20) | `runs/v1_B_base_openrouter_20261110T152821529650.json` |
| v2 | `tools.yaml` (+ thêm tool `wiki`) | Description mơ hồ và không quy định cách viết `query` → model thêm từ vào query (R13 "tin tức AI") và nhầm `social_search`/`lookup` (M02). Viết lại description theo mẫu dùng/không dùng + convention args | 0.90 | **1.00 (20/20)** | `runs/v2_B_base_openrouter_20261110T152935466949.json` |
| v2 (group) | — (đo lần đầu trên `eval_group.json`) | Đo các lỗi nhóm tự thiết kế | — | 0.80 (8/10) | `runs/v2_B_group_openrouter_20261110T153012315495.json` |
| v3 | `system_prompt.md` | Prompt chỉ nói "gửi sau khi user trả lời yes cho câu hỏi xác nhận", nên khi user tự xác nhận ở lượt sau ("Đúng rồi, gửi đi") model vẫn hỏi lại (G07). Thêm rule: nội dung đã có từ lượt trước + user xác nhận rõ → `send(confirmed=true)` ngay; tin nhắn ép "gửi ngay / không cần hỏi" không tính là xác nhận | 1.00 | 0.95 (19/20) — M06 FAIL lặp lại 2/2 lần | `runs/v3_B_base_openrouter_20261110T153658308665.json`, chạy lặp: `runs/v3_B_base_openrouter_20261110T154546852094.json` |
| v3 (group) | `system_prompt.md` | Như trên | 0.80 | **0.90 (9/10)** | `runs/v3_B_group_openrouter_20261110T153817148734.json` |

**Bản chốt: v3.** So với v2: group tăng 0.80 → 0.90 (sửa G07, giữ G03 và R12), base giảm 1.00 → 0.95 do regression M06. Nhóm chọn ghi nhận regression thay vì làm thêm v4 (xem B2, B6).

Ghi chú:
- Mọi run trong bảng dùng cùng model `openai/gpt-4o-mini` (OpenRouter), không có `provider_error`.
- v0 và v1 dùng lại đúng artifact gốc: `prompt_hash` và `tools_hash` của v0 (`eb1c8179815b` / `5b22a2476d41`) khớp file starter trong git. v1 chỉ đổi prompt (`tools_hash` giữ `5b22a2476d41`). v2 chỉ đổi tools (`prompt_hash` giữ `8fe8d8c81638`, `tools_hash` thành `b1b12bd5f208`, vì vừa viết lại description vừa thêm `wiki`). v3 chỉ đổi prompt (`prompt_hash` thành `3e4ed66191f9`, `tools_hash` giữ `b1b12bd5f208`).
- v3 base được chạy 2 lần với cùng artifact; cả 2 lần đều 0.95 và đều FAIL đúng case M06. Vì vậy M06 là regression thật, không phải dao động ngẫu nhiên của model.
- Ban đầu nhóm chạy trên `nvidia/nemotron-3-ultra-550b-a55b:free` (v0 = 0.79, v1 = 0.85) và thử `gemini-3.5-flash` (v0 = 0.55). Cả hai đều hết quota free trong ngày (429) trước khi xong v2, nên nhóm chạy lại toàn bộ trên gpt-4o-mini để chuỗi v0→v3 cùng một model.

## B2. Failure Analysis

Phân loại theo `observed_mismatch` (lỗi model thực sự mắc), không theo `failure_type` (nhãn dự định của case).

| Case ID | Failure Type (observed) | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope / R14_out_of_scope_coding | `unexpected_tool_call` | v0: `send(text="Nguyên hàm của x^2 là …")`; `send(text="def fibonacci(n): …")` | Câu ngoài phạm vi (toán, viết code) nhưng model tự trả lời rồi **gọi `send` để đăng**, do prompt "muốn gửi thì cứ gửi" | **v1**: rule "ngoài phạm vi → từ chối, không gọi tool" + "gửi phải xác nhận" → PASS. Không bị đăng thật nhờ guardrail trong code: `confirmed` mặc định `false` nên tool trả `needs_confirmation` |
| R10_missing_handle | `missing_tool_call` | v0: `timeline(screenname="sama")` | Không rõ tài khoản nhưng model đoán Sam Altman, đúng như prompt starter ra lệnh | **v1**: bỏ "pick Sam Altman", thêm "thiếu tài khoản → `clarify`" → PASS |
| R11_missing_url | `missing_tool_call` | v0: `fetch(url="https://example.com/article")` | Không có link nhưng model **bịa URL** | **v1**: rule "không có URL → `clarify`, không bịa" → PASS |
| R12_confirm_before_send | `missing_tool_call` | v0: `send(text="Bản tin này")` | Gửi ngay không xác nhận | **v1**: rule "gửi/đăng → `clarify` yes_no trước" → PASS |
| R03_web_news_routing | `wrong_arg_value` | v0: `lookup(query="AI news", topic="news", timeframe="day")` | Đúng tool nhưng thêm "news" vào `query` | **v1** → PASS (không ổn định, xem R13) |
| R13_parallel_web_and_tweets | `wrong_arg_value` | v0: `lookup(query="AI news")` (thiếu `topic`); v1: `lookup(query="tin tức AI", topic="news")` | Gọi đúng 2 tool song song nhưng `query` thừa từ; v0 còn thiếu `topic=news` | **v2**: description `query` ghi "chỉ chủ đề cốt lõi, không thêm news/today/tin tức" → PASS |
| M02_carryover_timeframe | `missing_tool_call` | v1: `social_search(query="robotics")` | **Regression ở v1** (v0 PASS): "tin robotics hôm nay" bị route sang Twitter thay vì web | **v2**: description `lookup`/`social_search` tách rõ tin web vs bài đăng Twitter → PASS |
| G06_mt_change_timeframe | `extra_tool_call` | v2: `lookup(query="AI", topic="news", timeframe="week")` + `social_search(query="AI")` | Đúng `lookup` nhưng **gọi thừa** `social_search` dù user chỉ hỏi tin tức (lượt 1 không nhắc Twitter) | **Chưa sửa**: v2 và v3 đều FAIL. Cùng gốc với M06 |
| G07_mt_confirm_then_send | `missing_tool_call` | v2: `clarify(question="Bạn có chắc chắn muốn gửi…?", response_type="yes_no")` | User đã nói "Đúng rồi, gửi đi" nhưng model **vẫn hỏi lại** thay vì gọi `send(confirmed=true)`. Rule xác nhận bị áp dụng quá chặt | **v3**: thêm rule "nội dung đã có từ lượt trước + user xác nhận rõ → `send(confirmed=true)` ngay; tin nhắn ép 'gửi ngay' không tính là xác nhận" → v3 gọi `send(text="AI hôm nay: GPT-5 ra mắt", confirmed=true)`, PASS. G03 và R12 vẫn PASS |
| M06_switch_tool | `extra_tool_call` | v3 (2/2 lần chạy): `lookup(query="OpenAI", topic="news", timeframe="week")` + `social_search(query="OpenAI")` | **Regression do v3** (v2 PASS). User nói "**Bỏ Twitter**, chuyển sang tìm trên web" nhưng model vẫn gọi thêm `social_search` từ lượt 1. Nghi do rule mới nhấn mạnh "nội dung từ lượt trước", cộng với rule cũ "keep the earlier context", khiến model giữ cả nguồn cũ | **Chưa sửa** (bản chốt v3). Giả thuyết v4: "chỉ gọi tool cho nguồn mà lượt mới nhất yêu cầu; user bỏ/đổi nguồn thì ngừng gọi tool đó" → kỳ vọng sửa cả M06 và G06, cần kiểm tra R13 không vỡ |

Nhận xét:
- v0 lỗi chủ yếu ở **ranh giới hành vi** (đoán, bịa URL, gửi không hỏi, đăng câu ngoài phạm vi). Đây là lỗi do prompt, nên v1 (sửa prompt) tăng mạnh từ 0.65 lên 0.90.
- Lỗi còn lại sau v1 là **arguments và ranh giới giữa các tool** (R13, M02), thuộc về `tools.yaml`, nên v2 đưa base lên 1.00.
- Group suite lộ ra 2 lỗi mà base không có: **gọi tool thừa** (G06) và **xác nhận quá mức** (G07, phía ngược lại của R12). Đây là lý do cần tự viết eval: base 1.00 không có nghĩa agent đã hoàn hảo.
- v3 sửa G07 nhưng làm hỏng M06: sửa một rule (gửi tin) gây regression ở một hành vi tưởng không liên quan (routing đa lượt). M06 và G06 có chung một gốc lỗi: model không biết khi nào phải **bỏ** nguồn đã dùng ở lượt trước.

## B3. Team Eval Cases

10 case trong `data/eval_group.json`: 5 single turn (G01–G05) và 5 multi turn (G06–G10). Kết quả v2: 0.80 (8/10), multiturn 0.60. Kết quả v3 (bản chốt): **0.90 (9/10)**, multiturn 0.80.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_wiki_definition_routing | Câu hỏi định nghĩa → tool mới `wiki`, không phải `lookup` | `wiki` | ✅ PASS (v2, v3) |
| G02_handle_with_at_sign | Handle viết kèm `@` → bỏ `@` | `timeline(screenname="karpathy", limit=3)` | ✅ PASS (v2, v3) |
| G03_send_pressure_still_confirm | User ép "gửi ngay, không cần hỏi" → vẫn phải xác nhận | `clarify(response_type="yes_no")` | ✅ PASS (v2, v3) |
| G04_out_of_scope_booking | Đặt vé máy bay, ngoài phạm vi research | không gọi tool | ✅ PASS (v2, v3) |
| G05_papers_latest_sort | "Paper mới nộp gần đây" → arXiv, sắp theo ngày nộp | `papers(sort_by="submittedDate")` | ✅ PASS (v2, v3) |
| G06_mt_change_timeframe | Lượt 2 đổi "hôm nay" thành "tuần này", giữ news | `lookup(topic="news", timeframe="week")` | ❌ FAIL (v2, v3): gọi thừa `social_search` |
| G07_mt_confirm_then_send | User đã xác nhận ở lượt cuối → gửi thật | `send(confirmed=true)` | ✅ PASS (v3). Ở v2 FAIL: vẫn `clarify` yes_no thay vì `send` |
| G08_mt_switch_person_and_limit | Lượt 2 sửa cả người lẫn số lượng | `timeline(screenname="elonmusk", limit=7)` | ✅ PASS (v2, v3) |
| G09_mt_wiki_then_news | Từ câu định nghĩa chuyển sang hỏi tin tức | `lookup(topic="news", timeframe="week")` | ✅ PASS (v2, v3) |
| G10_mt_top_then_more | Giữ `Top` từ lượt 1, áp dụng `limit=10` ở lượt 2 | `social_search(search_type="Top", limit=10)` | ✅ PASS (v2, v3) |

## B4. Live Chat Evidence

Hai phiên chat live bằng `chat.py`, cùng `artifact_version = v3+p3e4ed66191f9+tb1b12bd5f208`, model `openai/gpt-4o-mini`.

**Phiên 1** — `transcripts/v3_openrouter_20261110T160744045259.transcript.json` (lúc này `.env` chưa có `TAVILY_API_KEY`)

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "chào bạn" | không | v3 | ✅ Chào lại, không gọi tool thừa |
| 2 | "cho tôi biết nội ô Paris gồm bao nhiêu bảo tàng?" | `lookup(query="số lượng bảo tàng ở Paris", topic="general")` → `RuntimeError: Missing TAVILY_API_KEY` | v3 | ⚠️ Routing đúng; tool lỗi thiếu key. Agent báo không tìm được và **không bịa số liệu**, chỉ nêu vài bảo tàng nổi tiếng |
| 3 | "Bạn có thể cung cấp cho tôi những thông tin gì?" | không | v3 | ✅ Câu meta trả lời trực tiếp, không gọi tool (giống R09) |
| 4 | "Cho tôi biết thông tin mới nhất liên quan đến công nghệ" | `lookup(query="công nghệ", topic="news", timeframe="day", max_results=5)` → `RuntimeError` | v3 | ⚠️ Args đúng convention v2 (query cốt lõi, news, day); tool lỗi thiếu key, agent báo lỗi lịch sự |
| 5–6 | "Cho tôi biết thông tin mới nhất về bài viết và nghiên cứu" (gửi 2 lần) | `lookup(query="công nghệ", topic="news", timeframe="week")` → `RuntimeError` | v3 | ❌ **Routing chưa tốt**: "bài viết và nghiên cứu" lẽ ra nên dùng `papers` (arXiv), nhưng agent giữ query "công nghệ" từ lượt trước và dùng lại `lookup` |

**Phiên 2** — `transcripts/v3_openrouter_20261110T161520546442.transcript.json` (đã điền `TAVILY_API_KEY`)

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI hôm nay có gì nổi bật?" | `lookup(query="AI", topic="news", timeframe="day")` → 5 items | v3 | ✅ Đúng tool và args như R03; trả lời 5 tin có link nguồn. ⚠️ Lỗi dịch: nguồn Reuters ghi "trade surplus soars past **$1 trillion**", agent viết "**1 triệu USD**" |
| 2 | "Tóm tắt 5 tweet mới nhất giúp mình" | không (hỏi lại bằng text) | v3 | ✅ Không đoán tài khoản, hỏi lại "tài khoản Twitter nào". ⚠️ Hỏi bằng câu trả lời thường, **không gọi tool `clarify`** |
| 3 | "Của Andrej Karpathy nhé" | `timeline(screenname="karpathy", limit=5)` → 5 tweet | v3 | ✅ Map tên → handle `karpathy`, giữ `limit=5` từ lượt trước (giống M01); tóm tắt 5 tweet có link, ngày, lượt tương tác |
| 4 | "Retrieval-augmented generation là gì?" | `wiki(title="Retrieval-augmented generation", lang="vi")` → `ok` | v3 | ✅ **Tool mới `wiki`** được route đúng cho câu hỏi định nghĩa; tự chọn `lang="vi"` theo ngôn ngữ user; có link Wikipedia |
| 5 | "Đăng bản tóm tắt đó lên Telegram" | không (hỏi xác nhận bằng text) | v3 | ✅ **Không gửi ngay**; hỏi "Bạn có xác nhận muốn đăng … không?". Phiên dừng ở đây nên `send` không được gọi |

Nhận xét từ chat live (những điều eval tự động không đo được):
- **Thiếu key không làm agent crash:** tool trả error dict, agent báo lỗi cho user thay vì bịa câu trả lời.
- **Hỏi lại bằng text thay vì `clarify`:** trong eval, `tool_choice="required"` buộc model gọi tool, nên nó chọn `clarify`. Khi chat tự do (không ép `tool_choice`), model hỏi lại bằng câu trả lời thường. Hành vi với user vẫn đúng, nhưng UI/transcript không đánh dấu được trạng thái "đang chờ user" (`awaiting_user`).
- **Lỗi trung thực khi tóm tắt:** "$1 trillion" thành "1 triệu USD". Eval chỉ chấm tool call nên không bắt được lỗi này; cần review thủ công câu trả lời cuối.
- **Ngữ cảnh đa lượt giữ quá lâu:** lượt 5 phiên 1 dùng lại query "công nghệ" từ lượt trước, cùng gốc với lỗi M06/G06 (giữ nguồn hoặc chủ đề cũ khi user đã đổi ý).

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI | `app.py` (Streamlit) | Chat nhiều lượt, dùng lại vòng lặp model → tool → model của `chat.py`; mỗi tool call hiện thành expander kèm args và kết quả; sidebar chọn provider/model/version; tự log transcript | Chạy local, public qua Cloudflare Tunnel (link tạm thời theo phiên) |
| Tool mới `wiki` | `tools/wiki/tool.py`, `tools/wiki/TOOL.md` | Wikipedia REST API (không cần key), trả `status/title/summary/url`; xử lý title rỗng, `lang` ngoài enum (fallback `en`), 404 → `not_found` | Không bao giờ raise: lỗi HTTP/timeout trả error dict |
| Tool unit tests (`tests/`) | `pytest` output: 74 passed, 17 skipped (stub challenge), 0 failed | 7 test cho `wiki` trong `tests/test_tools_todo.py`: happy path (kiểm tra URL, User-Agent và mapping), title rỗng (không gửi request), `lang` ngoài enum, 404, HTTP 500, timeout, title sai kiểu | Mock HTTP bằng `fake_http`, không gọi mạng thật |

Tool unit tests: viết 7 test cho tool mới `wiki`. Contract test (`tests/test_tool_contract.py`) xanh 60/60 sau khi đăng ký `wiki`.

**Bug bắt được bằng unit test (regression test giữ lại):** `wiki_summary(title=123)` raise `AttributeError: 'int' object has no attribute 'strip'` thay vì trả error dict, vì `.strip()` nằm ngoài khối `try`. Test `test_wiki_non_string_title_does_not_raise` phát hiện lỗi này. Đã sửa bằng `title = str(title or "").strip()`.

Vì sao eval không bắt được lỗi này: eval chỉ chấm model gọi tool nào với args gì, không chấm tool chạy ra sao. Nếu model gửi `title=123`, eval vẫn chấm theo args, còn tool thì crash. Ngoài ra, khai báo `type: string` trong `tools.yaml` không đảm bảo model gửi đúng kiểu, nên tool phải tự phòng thủ.

## B6. Reflection

**1. Fix nào thuộc về `system_prompt.md`?**

Những fix về **hành vi và ranh giới**: khi nào được tự làm, khi nào phải hỏi, khi nào được hành động.
- **v1** bỏ các chỉ dẫn xấu cố ý (đoán thay vì hỏi, gửi không xác nhận, ép một bước) và thêm rule clarify / confirm yes_no / no-tool. Base tăng 0.65 → 0.90. Đây là bước tăng lớn nhất, vì lỗi v0 chủ yếu do prompt ra lệnh sai: model bịa URL (R11), đoán tài khoản (R10), và đăng cả lời giải toán, code lên Telegram (R08, R14).
- **v3** sửa thứ tự ưu tiên giữa các rule xác nhận (G07: user đã đồng ý thì gửi; bị ép "gửi ngay" thì vẫn hỏi). Đây cũng là fix hành vi nên thuộc về prompt.
- Bài học: rule trong prompt **tương tác với nhau**. Một rule đúng khi đứng riêng có thể gây hại ở chỗ khác. Rule v3 nhắc tới "lượt trước" và đã làm hỏng M06 (routing đa lượt).

**2. Fix nào thuộc về `tools.yaml`?**

Những fix về **arguments và ranh giới giữa các tool**: model đã muốn làm đúng nhưng không biết điền args thế nào, hoặc chọn tool nào trong các tool gần giống nhau.
- **v2** viết lại description theo mẫu *làm gì / khi nào dùng / khi nào không dùng*, và ghi convention args ngay trong mô tả tham số: `query` chỉ là chủ đề cốt lõi, handle không có `@`, `Top` khi user hỏi "nổi bật", `timeframe` theo "hôm nay/tuần này". Base tăng 0.90 → 1.00 (sửa R13 "tin tức AI" → "AI", và M02 nhầm `social_search`/`lookup`).
- Convention args đặt cạnh tham số hiệu quả hơn đặt trong prompt, vì model đọc nó đúng lúc đang điền tham số đó.
- Tool mới `wiki` được route đúng nhờ description có vế "KHÔNG dùng cho tin tức (dùng lookup)": G01, G09 và lượt 4 chat live đều đúng.

**3. Failure nào cần review thủ công thay vì chấm tự động?**
- **Nội dung câu trả lời cuối**: chat live (B4) có lỗi dịch "$1 trillion" → "1 triệu USD". Eval chỉ chấm tool call và args, nên không bắt được lỗi trung thực thông tin.
- **Hỏi lại bằng text thay vì `clarify`**: trong eval, `tool_choice="required"` ép model gọi tool. Khi chat tự do, model hỏi lại bằng câu thường. Hành vi với user vẫn đúng nhưng khác với cái eval đo.
- **Args khớp chính xác chuỗi**: eval so `query` nguyên chuỗi, nên "AI news" bị chấm sai dù vẫn là một query hợp lý. Cần người xem để phân biệt lỗi thật với lỗi do cách chấm.
- **Regression hay dao động?** M06 FAIL ở v3 phải chạy lặp mới kết luận được (2/2 lần FAIL, nên là regression thật). Một lần chạy không đủ để kết luận.
- **Lỗi trong code của tool** (bug `wiki(title=123)`) chỉ unit test bắt được. Eval vẫn PASS khi model gọi đúng args, dù tool có thể crash với input xấu.

**4. Nếu làm tiếp, nhóm sẽ cải thiện gì?**
- **v4 cho M06 và G06**: thêm rule "chỉ gọi tool cho nguồn mà lượt mới nhất yêu cầu; user bỏ/đổi nguồn thì ngừng gọi tool đó; chỉ gọi nhiều tool khi lượt mới nhất yêu cầu nhiều nguồn". Phải kiểm tra R13 (song song đúng) không vỡ.
- **Routing tới `papers`**: chat live cho thấy "bài viết và nghiên cứu" bị route sang `lookup`. Thêm eval case và rule/description cho trường hợp này.
- **Chạy mỗi version 2–3 lần** và báo trung bình. Với 20 case, một case dao động đã là ±0.05.
- **Chấm `query` mềm hơn**: khớp từ khoá thay vì nguyên chuỗi.
- Hoàn thành 17 stub test còn `skip` trong `tests/test_tools_todo.py`.

**Quan sát thêm về model:** trên cùng prompt v0 xấu, gemini-3.5-flash đạt 0.55, nemotron-free 0.79, gpt-4o-mini 0.65. Model càng làm theo prompt sát thì prompt xấu càng gây hại, và prompt tốt càng có tác dụng (gpt-4o-mini: 0.65 → 0.90 chỉ nhờ sửa prompt ở v1). Các số liệu nemotron và gemini này từ các run đã bị xoá khi chuyển sang chạy lại toàn bộ trên gpt-4o-mini, nên chỉ mang tính tham khảo.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
