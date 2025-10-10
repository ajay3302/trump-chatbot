# app.py
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Page setup ----------
st.set_page_config(page_title="Trump-Inspired Chatbot 🇺🇸", page_icon="🇺🇸")
st.title("🇺🇸 Trump-Inspired Chatbot")
st.caption("An AI speaking in a confident, business-leader style inspired by Donald Trump (not the real person).")
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/5/56/Donald_Trump_official_portrait.jpg",
    width=200,
    caption="Trump-Inspired Chatbot – Think Big, Win Big!"
)


# ---------- API key loading (Cloud → Env → .env → paste box) ----------
def _clean_key(k: str | None) -> str | None:
    if not k:
        return None
    k = k.strip()
    # if someone pasted with quotes, remove them
    if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
        k = k[1:-1].strip()
    return k

# 1) Streamlit Secrets (best for Streamlit Cloud)
api_key = _clean_key(st.secrets.get("OPENAI_API_KEY", None)) if hasattr(st, "secrets") else None

# 2) Environment variables (local or cloud)
if not api_key:
    api_key = _clean_key(os.getenv("OPENAI_API_KEY"))

# 3) .env file (local dev)
if not api_key:
    APP_DIR = Path(__file__).parent.resolve()
    ENV_PATH = APP_DIR / ".env"
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    api_key = _clean_key(os.getenv("OPENAI_API_KEY"))

# 4) Fallback: paste once
if not api_key:
    st.warning("API key not found. Paste your OpenAI API key below to continue.")
    with st.form("keyform"):
        typed = st.text_input("OPENAI_API_KEY", type="password", placeholder="sk-...")
        submit = st.form_submit_button("Use this key")
    if submit and typed:
        api_key = _clean_key(typed)
        os.environ["OPENAI_API_KEY"] = api_key  # make available to SDK in this process

if not api_key or not api_key.startswith("sk-"):
    st.error(
        "OpenAI API key missing or invalid.\n\n"
        "• On Streamlit Cloud: click **⚙️ Manage app → Settings → Secrets** and set\n"
        '  OPENAI_API_KEY = "sk-..."\n'
        "• Locally: create a `.env` next to `app.py` with one line:\n"
        "  OPENAI_API_KEY=sk-your-real-key\n\n"
        "Then click **⋮ → Rerun**."
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
    "Guardrails: no political opinions, impersonation, sensitive or unsafe content. "
    "Focus on motivation, business, success, and personal growth. Stay friendly and fun."
)

# ---------- Chat history ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! Let's talk success, business, and winning — bigly!"}
    ]

# show history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Chat input ----------
user_text = st.chat_input("Type your message…")
if user_text:
    # user bubble
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # assistant reply (non-streaming for simplicity/reliability)
    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            messages=[
                {"role": "system", "content": STYLE_CARD},
                {"role": "system", "content": GUARDRAILS},
                *st.session_state.messages,  # includes user message and prior turns
            ],
        )
        full_response = resp.choices[0].message.content
        st.markdown(full_response)

    # save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": full_response})

