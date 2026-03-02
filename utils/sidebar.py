"""
utils/sidebar.py — Shared sidebar for all AgriChain pages.
Renders branding, language selector, and navigation links.
The selected language persists in session_state across pages.
"""
import streamlit as st


def render_sidebar(current_page: str = "") -> str:
    """
    Render the unified sidebar. Returns the selected language code ('en', 'hi', 'mr').
    
    current_page: one of 'home', 'harvest', 'mandi', 'spoilage', 'map'
                  — that link will be visually highlighted.
    """
    _LANG_MAP = {"English": "en", "हिंदी": "hi", "मराठी": "mr"}

    if "app_language" not in st.session_state:
        st.session_state.app_language = "en"

    with st.sidebar:
        # Hide default Streamlit page navigation
        st.markdown("""
        <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # ── Branding ──────────────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;padding:0 0 12px;">
            <span style="font-size:2.2rem;">🌾</span>
            <div style="font-size:1.3rem;font-weight:800;color:#52b788;margin-top:2px;">AgriChain</div>
            <div style="font-size:0.72rem;color:#4a7a4a;margin-top:2px;">Farm-to-Market Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Language selector ─────────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.1em;color:#6ee86e;margin-bottom:6px">🌐 भाषा / Language</div>',
            unsafe_allow_html=True,
        )
        lang_choice = st.radio(
            "Language",
            list(_LANG_MAP.keys()),
            index=list(_LANG_MAP.values()).index(st.session_state.app_language)
                  if st.session_state.app_language in _LANG_MAP.values() else 0,
            key="sidebar_lang_radio",
            label_visibility="collapsed",
        )
        st.session_state.app_language = _LANG_MAP[lang_choice]

        st.markdown("---")

        # ── Navigation links ─────────────────────────────────────────────────
        _PAGES = [
            ("home",    "🏠", "Home",               "app.py"),
            ("harvest", "🌾", "Harvest Window",     "pages/1_🌾_Harvest.py"),
            ("mandi",   "🏪", "Mandi Ranker",       "pages/2_🏪_Mandi.py"),
            ("spoilage","⚠️", "Spoilage Assessor",  "pages/3_⚠️_Spoilage.py"),
            ("spoilage_prev","🛡️","Spoilage Prevention","pages/2_Spoilage_Prevention.py"),
            ("map",     "🗺️", "Map Explorer",       "pages/4_Map_Explorer.py"),
            ("ai_chat", "🤖", "AI Chat",            "pages/5_🤖_AI_Chat.py"),
        ]

        for key, icon, label, path in _PAGES:
            try:
                st.page_link(path, label=f"{icon}  {label}")
            except Exception:
                pass  # page may not exist yet

        st.markdown("---")

    return st.session_state.app_language
