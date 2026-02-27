"""
utils/green_theme.py — Dark green theme CSS injection.
"""
import streamlit as st


def inject_theme():
    """Inject the global dark-green CSS theme."""
    st.markdown("""
    <style>
    .stApp { background: #0d1117 !important; }
    section[data-testid="stSidebar"] { background: #0a0f15 !important; border-right: 1px solid #1e2833; }
    [data-testid="stHeader"] { background: #0d1117 !important; }
    h1, h2, h3, h4 { color: #e6edf3 !important; }
    p { color: #c9d1d9; }
    </style>
    """, unsafe_allow_html=True)
