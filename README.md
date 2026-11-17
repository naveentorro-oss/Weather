# Website

This repository contains a static website and a live weather dashboard.

## Run the weather dashboard with Streamlit

1. Create a Streamlit Community Cloud app from this GitHub repository.
2. Select `main` as the branch and `streamlit_app.py` as the app file.
3. Deploy. Streamlit installs the dependencies from `requirements.txt` and embeds the existing `Live Weather.html` dashboard.

The weather dashboard uses the public Open-Meteo, RainViewer, Leaflet, and OpenStreetMap services and requires an internet connection.

For the static website, open `Index.html`; its **Live Weather** navigation link opens the standalone dashboard.
