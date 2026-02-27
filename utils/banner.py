"""
utils/banner.py – Load and display banner images using base64 encoding.
"""
import streamlit as st
import base64
from pathlib import Path


def show_banner(image_name: str, alt: str = "Banner"):
    """Display a banner image from static/images directory via base64 encoding."""
    img_path = Path(__file__).parent.parent / "static" / "images" / image_name
    if img_path.exists():
        data = base64.b64encode(img_path.read_bytes()).decode()
        st.markdown(f"""
        <div style="border-radius:18px;overflow:hidden;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
            <img src="data:image/png;base64,{data}" alt="{alt}"
                 style="width:100%;height:auto;display:block;">
        </div>
        """, unsafe_allow_html=True)
