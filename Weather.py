import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Live Weather", page_icon="🌦️", layout="wide")

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_json(url: str, params: dict):
    response = requests.get(url, params=params, timeout=(5, 60))
    response.raise_for_status()
    return response.json()


def weather_label(code):
    return WEATHER_CODES.get(code, f"Unknown ({code})")


def format_temp(value):
    return "N/A" if value is None else f"{float(value):.1f}°C"


def format_speed(value):
    return "N/A" if value is None else f"{float(value):.1f} km/h"


def format_precip(value):
    return "N/A" if value is None else f"{float(value):.1f} mm"


def format_time(value):
    if not value:
        return "N/A"
    return datetime.fromisoformat(value).strftime("%a %H:%M")


def get_radar_image_url():
    try:
        radar_api = fetch_json("https://api.rainviewer.com/public/weather-maps.json", {})
    except (requests.RequestException, ValueError):
        return None

    past = radar_api.get("radar", {}).get("past") or []
    if not past:
        return None

    latest = past[-1]
    path = (latest.get("path") or "").strip()
    if not path:
        return None

    if path.startswith("http"):
        return path
    if path.startswith("/"):
        return f"https://tilecache.rainviewer.com{path}/256/1_0_0.png"
    return None


st.title("🌦️ Live Weather")
city = st.text_input("Search city", value="Bengaluru")

if city.strip() == "":
    st.warning("Type a city name to load the forecast.")
    st.stop()

try:
    geocode = fetch_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
    )
except requests.RequestException as exc:
    st.error(f"Unable to contact the geocoding service: {exc}")
    st.stop()

results = geocode.get("results")
if not results:
    st.error("No matching city was found. Try another name.")
    st.stop()

location = results[0]
lat = location["latitude"]
lon = location["longitude"]

forecast_params = {
    "latitude": lat,
    "longitude": lon,
    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
    "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,weather_code,pressure_msl,surface_pressure,cloud_cover,wind_speed_10m,wind_direction_10m",
    "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,rain_sum,showers_sum,snowfall_sum,wind_speed_10m_max",
    "forecast_days": 7,
    "forecast_hours": 24,
    "timezone": "auto",
}

with st.spinner(f"Loading weather for {location['name']}..."):
    try:
        weather = fetch_json("https://api.open-meteo.com/v1/forecast", forecast_params)
    except requests.RequestException as exc:
        st.error(f"Unable to contact the weather service: {exc}")
        st.stop()

if "current" not in weather or "hourly" not in weather or "daily" not in weather:
    st.error("The weather service returned incomplete data.")
    st.stop()

st.subheader(f"{location['name']}, {location['country']}")
st.caption(f"Local time: {datetime.fromisoformat(weather['current']['time']).strftime('%A, %b %d, %Y %H:%M')}")

st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

current = weather["current"]
current_cols = st.columns(5)
stats = [
    ("Temperature", format_temp(current.get("temperature_2m"))),
    ("Feels like", format_temp(current.get("apparent_temperature"))),
    ("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%"),
    ("Wind", format_speed(current.get("wind_speed_10m"))),
    ("Condition", weather_label(current.get("weather_code"))),
]
for col, (label, value) in zip(current_cols, stats):
    col.metric(label, value)

st.markdown("### Current conditions")
current_grid = {
    "Weather": weather_label(current.get("weather_code")),
    "Temperature": format_temp(current.get("temperature_2m")),
    "Feels like": format_temp(current.get("apparent_temperature")),
    "Humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
    "Precipitation": format_precip(current.get("precipitation")),
    "Rain": format_precip(current.get("rain")),
    "Showers": format_precip(current.get("showers")),
    "Snowfall": format_precip(current.get("snowfall")),
    "Cloud cover": f"{current.get('cloud_cover', 'N/A')} %",
    "Pressure": f"{current.get('surface_pressure', 'N/A')} hPa",
    "Wind speed": format_speed(current.get("wind_speed_10m")),
    "Wind direction": f"{current.get('wind_direction_10m', 'N/A')}°",
    "Wind gusts": format_speed(current.get("wind_gusts_10m")),
}

st.dataframe(
    pd.DataFrame([current_grid]).T.rename_axis("Metric").reset_index().rename(columns={"index": "Metric", 0: "Value"}),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Radar / precipitation")
radar_url = get_radar_image_url()
if radar_url:
    st.image(radar_url, caption="Latest radar snapshot")
else:
    hourly = weather["hourly"]
    radar_rows = []
    for idx in range(min(len(hourly.get("time", [])), 24)):
        value = hourly.get("precipitation", [None])[idx]
        if value is not None:
            radar_rows.append({
                "Time": format_time(hourly["time"][idx]),
                "Precipitation": float(value),
            })

    if radar_rows:
        radar_df = pd.DataFrame(radar_rows).set_index("Time")
        st.line_chart(radar_df)
        peak_precip = radar_df["Precipitation"].max()
        st.caption(f"Radar-style precipitation trend: peak {peak_precip:.1f} mm in the next 24 hours.")
    else:
        st.info("No precipitation radar data is available for this location.")

st.markdown("### Hourly forecast")
hourly = weather["hourly"]
rows = []
for idx in range(min(len(hourly.get("time", [])), 24)):
    rows.append(
        {
            "Time": format_time(hourly["time"][idx]),
            "Temp": format_temp(hourly.get("temperature_2m", [None])[idx]),
            "Feel": format_temp(hourly.get("apparent_temperature", [None])[idx]),
            "Humidity": f"{hourly.get('relative_humidity_2m', [None])[idx]}%" if hourly.get("relative_humidity_2m", [None])[idx] is not None else "N/A",
            "Rain": format_precip(hourly.get("precipitation", [None])[idx]),
            "Chance": f"{hourly.get('precipitation_probability', [None])[idx]}%" if hourly.get("precipitation_probability", [None])[idx] is not None else "N/A",
            "Wind": format_speed(hourly.get("wind_speed_10m", [None])[idx]),
            "Condition": weather_label(hourly.get("weather_code", [None])[idx]),
        }
    )

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("### Daily forecast")
daily = weather["daily"]
forecast_rows = []
for idx in range(len(daily.get("time", []))):
    forecast_rows.append(
        {
            "Day": datetime.fromisoformat(daily["time"][idx]).strftime("%a %b %d"),
            "Condition": weather_label(daily.get("weather_code", [None])[idx]),
            "High": format_temp(daily.get("temperature_2m_max", [None])[idx]),
            "Low": format_temp(daily.get("temperature_2m_min", [None])[idx]),
            "Rain": format_precip(daily.get("precipitation_sum", [None])[idx]),
            "Wind": format_speed(daily.get("wind_speed_10m_max", [None])[idx]),
            "Sunrise": datetime.fromisoformat(daily["sunrise"][idx]).strftime("%H:%M") if daily.get("sunrise") else "N/A",
            "Sunset": datetime.fromisoformat(daily["sunset"][idx]).strftime("%H:%M") if daily.get("sunset") else "N/A",
        }
    )

st.dataframe(pd.DataFrame(forecast_rows), use_container_width=True, hide_index=True)

st.caption("Weather data is powered by Open-Meteo and radar imagery from RainViewer when available.")
