import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv
from modules.ai_assistant import get_ai_response, build_context
from utils.translator import t
from utils.sidebar import render_sidebar

load_dotenv()

st.set_page_config(page_title="AI Chat — AgriChain", page_icon="🤖", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fefae0 !important; color: #1b1b1b !important; }
.stApp { background-color: #fefae0 !important; }
[data-testid="stAppViewContainer"] { background-color: #fefae0 !important; }
[data-testid="stHeader"] { background-color: #fefae0 !important; border-bottom: 1px solid #d4e6c3 !important; }
section[data-testid="stSidebar"] { background-color: #1a3d2e !important; border-right: 1px solid #2d6a4f; }
section[data-testid="stSidebar"] > div { padding: 1.2rem 1rem; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div { color: #d4f0c0 !important; }

.page-header {
    background: linear-gradient(135deg, #2d6a4f 0%, #1a3d2e 100%);
    border-radius: 20px;
    padding: 32px 36px;
    margin-bottom: 28px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 4px 20px #2d6a4f22;
}
.page-header-icon { font-size: 3rem; flex-shrink: 0; }
.page-header h1   { font-size: 2.2rem; font-weight: 900; color: #fff; margin: 0; line-height: 1.1; }
.page-header p    { font-size: 0.95rem; color: #a8d5ba; margin: 6px 0 0; }


.chat-msg-user {
    background: linear-gradient(135deg, #2d6a4f, #1a3d2e);
    border-radius: 14px 14px 4px 14px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.8rem;
    font-size: 0.92rem;
    color: #fff;
    text-align: right;
    max-width: 80%;
    margin-left: auto;
    box-shadow: 0 2px 8px #2d6a4f18;
}
.chat-msg-ai {
    background: #f0f9f0;
    border: 1px solid #d4e6c3;
    border-radius: 14px 14px 14px 4px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.8rem;
    font-size: 0.92rem;
    color: #333;
    line-height: 1.7;
    max-width: 80%;
    box-shadow: 0 2px 8px #2d6a4f08;
}

.context-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #d4edda;
    border: 1px solid #4caf50;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #155724;
    margin-bottom: 1rem;
}
.no-context-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #856404;
    margin-bottom: 1rem;
}

.stButton > button { background-color: #2d6a4f; color: #fff; font-weight: 700; border: none; border-radius: 8px; }
.stButton > button:hover { background-color: #1a3d2e; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
lang = render_sidebar(current_page="ai_chat")

# ─── Session state init ──────────────────────────────────────────────────────
for k, v in [("chat_history", []), ("ai_context", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()

# ─── Page Header ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-header-icon">🤖</div>
  <div>
    <h1 style="color:#fff !important">{t('AgriChain AI Assistant', lang)}</h1>
    <p>{t('Ask questions about your crops, prices, weather, and harvest strategy.', lang)}</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Context status ──────────────────────────────────────────────────────────
has_context = bool(st.session_state.ai_context)
if has_context:
    st.markdown(
        f'<div class="context-badge">✅ {t("Farm analysis loaded — AI has your crop data context", lang)}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="no-context-badge">💡 {t("Run analysis on the Home page first for personalised AI advice", lang)}</div>',
        unsafe_allow_html=True,
    )

# ─── Quick prompts ────────────────────────────────────────────────────────────
st.markdown(f'<div style="font-size:0.72rem;font-weight:700;color:#2d6a4f;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">{t("Quick Questions", lang)}</div>', unsafe_allow_html=True)

quick_prompts = [
    t("When should I sell my crop?", lang),
    t("What is the best storage method?", lang),
    t("How does weather affect my harvest?", lang),
    t("How can I get the best price?", lang),
]

qp_cols = st.columns(len(quick_prompts))
quick_msg = None
for i, (col, prompt) in enumerate(zip(qp_cols, quick_prompts)):
    with col:
        if st.button(prompt, key=f"qp_{i}", use_container_width=True):
            quick_msg = prompt

# ─── Chat area ────────────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    css = "chat-msg-user" if msg["role"] == "user" else "chat-msg-ai"
    pfx = "🧑‍🌾" if msg["role"] == "user" else "🤖"
    st.markdown(f'<div class="{css}">{pfx} {msg["content"]}</div>', unsafe_allow_html=True)

# ─── Input form ───────────────────────────────────────────────────────────────
with st.form(key="chat_form", clear_on_submit=True):
    ci, cs = st.columns([5, 1])
    with ci:
        user_input = st.text_input(
            "Ask AI",
            placeholder=t("Ask anything about farming, prices, weather...", lang),
            label_visibility="collapsed",
        )
    with cs:
        send_btn = st.form_submit_button(f"↑ {t('Send', lang)}")

# Handle quick prompt click
if quick_msg:
    user_input = quick_msg
    send_btn = True

if send_btn and user_input and user_input.strip():
    if not groq_api_key:
        st.warning(t("Please add your Groq API key in .env to use the AI assistant.", lang))
    else:
        with st.spinner(f"🤖 {t('AgriChain AI is thinking...', lang)}"):
            try:
                response = get_ai_response(
                    api_key=groq_api_key,
                    user_message=user_input.strip(),
                    context=st.session_state.ai_context,
                    chat_history=st.session_state.chat_history,
                )
                st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()
            except Exception as e:
                st.error(f"AI error: {str(e).encode('ascii', errors='replace').decode('ascii')}")

# ─── Clear chat button ───────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button(f"🗑️ {t('Clear Chat', lang)}", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()
