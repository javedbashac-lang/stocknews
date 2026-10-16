import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

IST = ZoneInfo("Asia/Kolkata")
DATA_FILE = Path(__file__).with_name("news.json")

st.set_page_config(
    page_title="Global News → Indian Markets",
    page_icon="🌍",
    layout="wide",
)

st.markdown("""
<style>
.block-container {max-width: 1100px; padding-top: 1.5rem;}
.news-card {padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.3);
            border-radius: 12px; margin-bottom: .8rem;}
.small-muted {color: #777; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)


def load_news():
    if not DATA_FILE.exists():
        return {"updated_at": None, "items": []}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"updated_at": None, "items": []}


now = datetime.now(IST)
data = load_news()

st.title("🌍 Global News → Indian Stock Market")
st.caption("A concise daily briefing on global developments that may influence Indian markets.")
c1, c2, c3 = st.columns([1, 1, 1])
c1.metric("Briefing", f"{len(data.get('items', []))} stories")
c2.metric("Current time (IST)", now.strftime("%d %b %Y · %I:%M %p"))
updated = data.get("updated_at")
c3.metric("Last data refresh", updated or "Not available")

st.info("Impact labels are rule-based estimates, not guaranteed market predictions. Read the linked article before making decisions.")

if st.button("↻ Refresh news now", type="primary"):
    st.cache_data.clear()
    st.rerun()

items = data.get("items", [])
if not items:
    st.warning(
        "No briefing file found yet. Run `python refresh_news.py` once, then restart the app. "
        "The scheduled GitHub Action can keep the briefing updated after setup."
    )
else:
    impacts = ["All", "Positive", "Negative", "Mixed"]
    selected = st.selectbox("Filter by estimated market impact", impacts)
    shown = [x for x in items if selected == "All" or x.get("impact") == selected]

    for i, item in enumerate(shown, 1):
        impact = item.get("impact", "Mixed")
        impact_emoji = {"Positive": "🟢", "Negative": "🔴", "Mixed": "🟠"}.get(impact, "🟠")
        title = item.get("title", "Untitled story")
        source = item.get("source", "News source")
        published = item.get("published", "")
        affected = ", ".join(item.get("affected_areas", [])) or "Broad market sentiment"

        with st.container(border=True):
            st.markdown(f"### {i}. [{title}]({item.get('url', '#')})")
            st.caption(f"{source} · {published}")
            st.markdown(f"**Estimated impact:** {impact_emoji} {impact}  ·  **Areas:** {affected}")
            st.write(item.get("why_it_matters", "May influence global risk sentiment and Indian markets."))

st.divider()
st.caption(
    "Schedule: 7:00 AM and 9:00 PM IST daily. Automated schedule runs through GitHub Actions "
    "(1:30 UTC and 15:30 UTC). Weekend and holiday news may still affect the next trading session."
)
