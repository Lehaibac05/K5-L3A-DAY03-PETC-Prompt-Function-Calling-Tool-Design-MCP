"""Streamlit UI for the Research Agent.

Reuses the same model -> tool -> model loop as chat.py, so behaviour in the UI
matches the CLI chat, and every turn is logged to transcripts/*.transcript.json.

Run:  streamlit run app.py   (→ http://localhost:8501)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")

# ---------------- Sidebar: config ----------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model_override = st.text_input("Model (để trống = mặc định / .env)", value="")
    version = st.text_input("Version label", value="v0")
    prompt_path = Path(st.text_input("System prompt", value=str(ARTIFACTS_DIR / "system_prompt.md")))
    tools_path = Path(st.text_input("Tools YAML", value=str(ARTIFACTS_DIR / "tools.yaml")))
    if st.button("🗑️ Cuộc trò chuyện mới", use_container_width=True):
        for key in ("transcript", "transcript_path", "history", "turns_ui", "config_key"):
            st.session_state.pop(key, None)
        st.rerun()


@st.cache_resource(show_spinner=False)
def load_runtime(provider_name: str, prompt_path: str, tools_path: str, version: str):
    provider = make_provider(provider_name)
    system_prompt = Path(prompt_path).read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(Path(tools_path))
    openai_tools = to_openai_tools(tool_declarations)
    artifact_version = build_artifact_version(version, Path(prompt_path), Path(tools_path))
    return provider, system_prompt, tool_declarations, openai_tools, artifact_version


try:
    provider, system_prompt, tool_declarations, openai_tools, artifact_version = load_runtime(
        provider_name, str(prompt_path), str(tools_path), version
    )
except Exception as exc:  # show config errors in the UI instead of a stack trace
    st.error(f"Không khởi tạo được agent: {type(exc).__name__}: {exc}")
    st.stop()

model = model_override.strip() or None
selected_model = model or getattr(provider, "default_model", None)

# New transcript whenever the config changes.
config_key = (provider_name, selected_model, version, str(prompt_path), str(tools_path))
if st.session_state.get("config_key") != config_key:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    st.session_state.config_key = config_key
    st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model,
        "source": "streamlit_ui",
        "system_prompt": str(prompt_path),
        "tools": str(tools_path),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.history = []
    st.session_state.turns_ui = []

with st.sidebar:
    st.divider()
    st.caption(f"**Model:** `{selected_model}`")
    st.caption(f"**Artifact:** `{artifact_version.artifact_version}`")
    st.caption(f"**Transcript:** `{st.session_state.transcript_path.name}`")
    with st.expander(f"🧰 {len(tool_declarations)} tools"):
        for item in tool_declarations:
            st.markdown(f"- **`{item['name']}`** — {item.get('description', '')}")

# ---------------- Main: chat ----------------
st.title("🔎 Research Agent")
st.caption("Agent chọn tool, gọi tool thật và trả lời dựa trên kết quả. Mọi lượt được log vào transcript JSON.")


def render_tool_events(rounds: list[dict[str, Any]]) -> None:
    for rnd in rounds:
        for event in rnd.get("tool_results", []):
            name = event.get("tool")
            args = json.dumps(event.get("args", {}), ensure_ascii=False)
            with st.expander(f"🔧 Round {rnd.get('round')}: `{name}({args})`"):
                st.json(event.get("result", {}), expanded=False)


for turn in st.session_state.turns_ui:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        render_tool_events(turn.get("rounds", []))
        if turn.get("status") == "provider_error":
            st.error(turn.get("error"))
        else:
            if turn.get("status") == "waiting_for_user":
                st.info("❓ Agent cần bạn bổ sung thông tin")
            st.markdown(turn.get("assistant_text") or "")

user_text = st.chat_input("Hỏi agent, ví dụ: Tin tức AI hôm nay có gì nổi bật?")
if user_text:
    transcript = st.session_state.transcript
    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    with st.spinner("Agent đang xử lý..."):
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            turn_record.update(result)
            st.session_state.history.append({"role": "user", "content": user_text})
            st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, transcript)
    st.session_state.turns_ui.append(turn_record)
    st.rerun()
