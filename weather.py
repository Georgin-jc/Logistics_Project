import requests

def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )

    try:
        data = requests.get(url, timeout=5).json()
        w = data.get("current_weather")
        if not w:
            return None

        return f"{w['temperature']}°C, Wind {w['windspeed']} km/h"
    except Exception:
        return None
