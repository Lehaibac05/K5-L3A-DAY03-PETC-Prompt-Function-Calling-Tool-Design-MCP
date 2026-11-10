from __future__ import annotations

from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
load_lab_env(ROOT)


def main() -> None:
    st.set_page_config(page_title="PETC Research Agent", page_icon="🔎", layout="centered")
    st.title("🔎 PETC Research Agent")
    st.caption("Tìm web/X, đọc URL, kiểm tra nguồn và tạo digest có trích dẫn.")

    with st.sidebar:
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
        model = st.text_input("Model override (optional)") or None
        version = st.text_input("Artifact version", value="v3")
        if st.button("Xóa hội thoại"):
            st.session_state.history = []
            st.rerun()

    if "history" not in st.session_state:
        st.session_state.history = []
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_text = st.chat_input("Ví dụ: Tin AI hôm nay có gì nổi bật?")
    if not user_text:
        return
    st.session_state.history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    try:
        system_prompt = (ARTIFACTS / "system_prompt.md").read_text(encoding="utf-8")
        messages = [{"role": "system", "content": system_prompt}, *st.session_state.history]
        with st.chat_message("assistant"):
            with st.spinner("Đang nghiên cứu..."):
                result = run_model_tool_loop(
                    provider=make_provider(provider_name),
                    messages=messages,
                    tools=to_openai_tools(load_tool_declarations(ARTIFACTS / "tools.yaml")),
                    model=model,
                    max_tool_rounds=4,
                )
            for event in result["tool_events"]:
                with st.expander(f"Tool: {event['tool']}"):
                    st.json(event["result"])
            reply = result["assistant_text"]
            st.markdown(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})
    except Exception as exc:
        st.error(f"Không thể chạy agent: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
