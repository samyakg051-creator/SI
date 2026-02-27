"""
Run this ONCE to fix the Streamlit page URL conflict.
Usage: e:\rippl_effect\.venv\Scripts\python.exe fix_pages.py
"""
import os, shutil

PAGES = r"e:\rippl_effect\pages"

# The emoji-named file and the ASCII file both resolve to URL "Map_Explorer"
# Renaming the emoji file to start with _ excludes it from Streamlit discovery
src = os.path.join(PAGES, "4_\U0001f5fa\ufe0f_Map_Explorer.py")
dst = os.path.join(PAGES, "_disabled_map_explorer.py")

if os.path.exists(src):
    os.rename(src, dst)
    print(f"✅ Renamed:\n  {src}\n  → {dst}")
else:
    print(f"⚠️  File not found (may already be renamed): {src}")
    # List what IS in pages/
    print("\nFiles in pages/:")
    for f in os.listdir(PAGES):
        print(f"  {f}")

print("\nDone. Now restart: python -m streamlit run app.py")
