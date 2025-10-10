# app.py
import os
from pathlib import Path
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------- Page setup ----------------
st.set_page_config(page_title="Trump-Inspired Chatbot 🇺🇸", page_icon="🇺🇸")

col1, col2 = st.columns([1, 4])
with col1:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/5/56/Donald_Trump_official_portrait.jpg",
        width=110,
    )
with col2:
    st.title("🇺🇸 Donald Trump")
    st.caption("Make America Great Again")

# ---------------- API key loading ----------------
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
        "• Streamlit Cloud: ⚙️ Manage app → Settings → Secrets →\n"
        '  OPENAI_API_KEY = "sk-..."\n'
        "• Local: `.env` next to `app.py` with:\n"
        "  OPENAI_API_KEY=sk-your-real-key\n\n"
        "Then click ⋮ → Rerun."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------- Style & guardrails ----------------
STYLE_CARD = (
    "You are Donald Trump.\n"
    "All your personal details exactly match with Donald Trump.\n"
    "Primary goal: deliver useful, concrete advice. Secondary: a brief, witty closer only if it adds value.\n"
    "Avoid hype, empty slogans, and repeated phrases. Prefer specifics: numbers, examples, checklists.\n"
    "Keep answers short unless the user asks for depth.\n"
    "Use phrases like Make America Great Again, The Beautiful Bill, wherever needed. \n"
)

GUARDRAILS = (
    "Safety: no medical/financial/legal guarantees; no hate/harassment; no political persuasion. "
)

AVOID_NOTE = (
    "Avoid repeating slogans (e.g., 'believe me', 'tremendous', 'huge', 'win big', 'make it great again', 'bigly'). "
    "Vary word choice across the session. Do not restate the same advice multiple times."
)

# ---------------- Intent detection & tuning ----------------
FACT_KEYWORDS = r"\b(what|who|when|where|define|explain|difference|meaning|facts?|is|are|was|were|how much|price|cost)\b"
PLAN_KEYWORDS = r"\b(plan|strategy|roadmap|steps|how to|improve|grow|increase|optimize|launch|start|fix|reduce)\b"
MOTIVATE_KEYWORDS = r"\b(motivate|motivation|encourage|confidence|nervous|scared|stuck)\b"

def detect_mode(text: str) -> str:
    t = text.lower()
    if re.search(FACT_KEYWORDS, t):
        return "facts"
    if re.search(PLAN_KEYWORDS, t):
        return "advice"
    if re.search(MOTIVATE_KEYWORDS, t):
        return "motivation"
    # default to advice for usefulness
    return "advice"

def mode_instructions(mode: str) -> str:
    if mode == "facts":
        return (
            "Mode: FACTS.\n"
            "Respond neutrally and precisely. If appropriate, include a short 3–5 bullet summary. "
            "Cite sources only if the user provided them; otherwise keep to general knowledge. "
            "Optionally add one short confident closer if it adds value."
        )
    if mode == "advice":
        return (
            "Mode: ADVICE.\n"
            "Give a tight action plan with 3–6 numbered steps, concrete examples, and simple metrics "
            "(e.g., deadlines, targets, percentages). No slogans. No repetition."
        )
    # motivation
    return (
        "Mode: MOTIVATION.\n"
        "Keep it uplifting but grounded: 2–4 short sentences, then 3 actionable micro-steps the user can do today. "
        "One fresh one-liner max; do not recycle lines used earlier."
    )

# ---------------- Session state ----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask about business, growth, habits, or a quick plan — I’ll keep it practical."}
    ]
if "used_phrases" not in st.session_state:
    st.session_state.used_phrases = set()

def build_avoid_hint() -> str:
    if not st.session_state.used_phrases:
        return ""
    used_list = sorted(list(st.session_state.used_phrases))[:12]
    return "Already used this session, avoid repeating: " + "; ".join(used_list)

# ---------------- Render history ----------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------------- Chat input ----------------
user_text = st.chat_input("Type your message…")
if user_text:
    # Show user
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Build prompt
    mode = detect_mode(user_text)
    dynamic_avoid = build_avoid_hint()
    short_history = st.session_state.messages[-6:]  # shorter context reduces echo

    # Model call (tighter controls)
    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,        # lower = less absurdity
            top_p=0.85,
            presence_penalty=0.4,   # explore new ideas slightly
            frequency_penalty=1.2,  # push away from repeated wording
            max_tokens=450,         # keep answers tight
            messages=[
                {"role": "system", "content": STYLE_CARD},
                {"role": "system", "content": GUARDRAILS},
                {"role": "system", "content": AVOID_NOTE},
                {"role": "system", "content": mode_instructions(mode)},
                {"role": "system", "content": dynamic_avoid},
                *short_history,
            ],
        )
        full_response = resp.choices[0].message.content
        st.markdown(full_response)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Track common slogan-y phrases to avoid later
    for p in ["believe me", "win big", "make it great again", "tremendous", "huge", "bigly"]:
        if p.lower() in full_response.lower():
            st.session_state.used_phrases.add(p.lower())




