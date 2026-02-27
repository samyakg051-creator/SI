"""
utils/shared_state.py — Cross-page session state management.
"""
import streamlit as st

_DEFAULTS = {
    "crop": "Wheat",
    "district": "Pune",
    "sowing": None,
    "quantity": 50.0,
    "storage": "Cold Storage",
    "transit": 8,
}


def init_shared():
    """Initialize shared session state defaults."""
    for k, v in _DEFAULTS.items():
        if f"shared_{k}" not in st.session_state:
            st.session_state[f"shared_{k}"] = v


def get_shared(key: str):
    """Get a shared value with fallback to default."""
    return st.session_state.get(f"shared_{key}", _DEFAULTS.get(key))


def sync_all(**kwargs):
    """Sync values across pages."""
    for k, v in kwargs.items():
        if v is not None:
            st.session_state[f"shared_{k}"] = v
