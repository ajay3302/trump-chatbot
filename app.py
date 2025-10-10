# app.py
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Page setup ----------
st.set_page_config(page_title="Trump-Inspired Chatbot 🇺🇸", page_icon="🇺🇸")

st.title("🇺🇸 Trump-Inspired Chatbot")
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/5/56/Donald_Trump_official_portrait.jpg",
    width=200,
    caption="Trump-Inspired Chatbot – Think Big, Win Big!"
)

st.caption("An AI speaking in a confident, business-leader style inspired by Donald Trump (not the real person).")

# ---------- Load API key ----------
APP_DIR = Path(__file__).parent.resolve()
ENV_PATH = APP_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("API key not found. Paste your OpenAI API key below to continue.")
    with st.form("keyform"):
        typed = st.text_input("OPENAI_API_KEY", type="password", placeholder="sk-...")
        submit = st.form_submit_button("Use this key")
    if submit and typed:
        api_key = typed.strip()
        os.environ["OPENAI_API_KEY"] = api_key  # make available to OpenAI SDK

if not api_key:
    st.error(
        "Still no API key. Create a `.env` file next to `app.py` with one line:\n\n"
        "OPENAI_API_KEY=sk-your-real-key\n\n"
        "Or paste the key in the box above."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Style / guardrails ----------
STYLE_CARD = (
    "You are a charismatic, confident, high-energy business leader who speaks in a style inspired by Donald Trump.\n"
    "Use bold, simple, persuasive language with short sentences and punchy slogans.\n"
    "Be entertaining, humorous, and self-assured — but always respectful and light-hearted.\n"
    "You may boast about success, talk about winning, and motivate others to think big.\n"
    "Avoid political or controversial statements. Never claim to be any real person.\n"
    "Keep it conversational, direct, and full of optimism. End with a memorable one-liner if it fits."
)

GUARDRAILS = (
    "Guardrails: no political opinions, impersonation, or sensitive topics. "
    "Focus on motivation, business, success, and personal growth. Stay friendly and fun."
)

# ---------- Initialize chat history ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! Let's talk success, business, and winning — bigly!"}
    ]

# ---------- Display chat history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Chat input ----------
user_text = st.chat_input("Type your message…")
if user_text:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Generate AI reply (non-streaming for simplicity)
    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            messages=[
                {"role": "system", "content": STYLE_CARD},
                {"role": "system", "content": GUARDRAILS},
                *st.session_state.messages,
            ],
        )
        full_response = resp.choices[0].message.content
        st.markdown(full_response)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": full_response})
