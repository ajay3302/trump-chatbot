# app.py
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Page setup ----------
st.set_page_config(page_title="Trump-Inspired Chatbot 🇺🇸", page_icon="🇺🇸")

# Small header row with compact image + title
col1, col2 = st.columns([1, 4])
with col1:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/5/56/Donald_Trump_official_portrait.jpg",
        width=120,
    )
with col2:
    st.title("🇺🇸 Trump-Inspired Chatbot")
    st.caption("Confident, business-leader style inspired by Donald Trump — not the real person.")

# ---------- API key loading (Cloud → Env → .env → paste box) ----------
def _clean_key(k: str | None) -> str | None:
    if not k:
        return None
    k = k.strip()
    if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
        k = k[1:-1].strip()
    return k

api_key = _clean_key(st.secrets.get("OPENAI_API_KEY", None)) if hasattr(st, "secrets") else None
if not api_key:
    api_key = _clean_key(os.getenv("OPENAI_API_KEY"))
if not api_key:
    APP_DIR = Path(__file__).parent.resolve()
    ENV_PATH = APP_DIR / ".env"
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    api_key = _clean_key(os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.warning("API key not found. Paste your OpenAI API key below to continue.")
    with st.form("keyform"):
        typed = st.text_input("OPENAI_API_KEY", type="password", placeholder="sk-...")
        submit = st.form_submit_button("Use this key")
    if submit and typed:
        api_key = _clean_key(typed)
        os.environ["OPENAI_API_KEY"] = api_key

if not api_key or not api_key.startswith("sk-"):
    st.error(
        "OpenAI API key missing or invalid.\n\n"
        "• On Streamlit Cloud: ⚙️ Manage app → Settings → Secrets →\n"
        '  OPENAI_API_KEY = "sk-..."\n'
        "• Locally: create `.env` next to `app.py` with:\n"
        "  OPENAI_API_KEY=sk-your-real-key\n\n"
        "Then click ⋮ → Rerun."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Style / guardrails (with anti-repetition cues) ----------
STYLE_CARD = (
    "You are a charismatic, confident, high-energy business leader who speaks in a style inspired by Donald Trump.\n"
    "Use bold, simple, persuasive language with short sentences and punchy slogans.\n"
    "Be entertaining, humorous, and self-assured — but always respectful and light-hearted.\n"
    "Avoid political or controversial statements. Never claim to be any real person.\n"
    "IMPORTANT: Vary your wording. Do not repeat the same slogans or catchphrases in this session.\n"
    "Avoid overusing words like tremendous/huge/winning/believe me. Prefer fresh phrasing each answer.\n"
    "Keep it conversational, direct, and optimistic. End with a memorable one-liner only if it is NEW."
)
GUARDRAILS = (
    "Guardrails: no political opinions, impersonation, or unsafe content. "
    "Focus on motivation, leadership, business, habits, and personal growth. Keep it friendly and fun."
)
AVOID_NOTE = (
    "Avoid these phrases unless explicitly requested: "
    "'believe me', 'win big', 'make it great again', 'tremendous', 'huge', 'bigly'."
)

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me about business, leadership, habits, or motivation."}
    ]

# (Optional) track used slogans to help avoid repeats further
if "used_phrases" not in st.session_state:
    st.session_state.used_phrases = set()

def build_avoid_hint() -> str:
    if not st.session_state.used_phrases:
        return ""
    used_list = sorted(list(st.session_state.used_phrases))[:12]
    return "Already used this session, avoid repeating: " + "; ".join(used_list)

# ---------- Render history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Chat input ----------
user_text = st.chat_input("Type your message…")
if user_text:
    # 1) user bubble
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # 2) assistant reply with anti-repetition settings + short history
    with st.chat_message("assistant"):
        short_history = st.session_state.messages[-6:]  # limit context to reduce echo loops
        dynamic_avoid = build_avoid_hint()

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,       # a bit tighter to reduce rambling
            top_p=0.9,
            presence_penalty=0.3,  # encourage new ideas
            frequency_penalty=1.0, # strongly discourage repeating wording
            messages=[
                {"role": "system", "content": STYLE_CARD},
                {"role": "system", "content": GUARDRAILS},
                {"role": "system", "content": AVOID_NOTE},
                {"role": "system", "content": dynamic_avoid},
                *short_history,
            ],
        )
        full_response = resp.choices[0].message.content
        st.markdown(full_response)

    # 3) save reply and record any repeated phrases heuristically
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # naive phrase capture (adjust or remove as you like)
    for p in ["believe me", "win big", "make it great again", "tremendous", "huge", "bigly"]:
        if p.lower() in full_response.lower():
            st.session_state.used_phrases.add(p.lower())
