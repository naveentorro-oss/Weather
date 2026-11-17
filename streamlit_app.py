from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Live Weather", page_icon="🌦️", layout="wide")
st.title("🌦️ Live Weather")
st.caption("Current conditions, precipitation radar, and hourly and daily forecasts.")

weather_page = Path(__file__).parent / "Live Weather.html"
try:
    weather_html = weather_page.read_text(encoding="utf-8")
except OSError as error:
    st.error(f"Could not load the weather app ({error}). Make sure Live Weather.html is in the repository root.")
else:
    # The existing standalone weather page runs inside this iframe without needing a rewrite.
    components.html(weather_html, height=1600, scrolling=True)
