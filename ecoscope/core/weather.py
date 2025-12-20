import requests

def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,temperature_2m",
        "forecast_days": 3,
        "timezone": "Africa/Tunis",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def next_hours(weather_json, hours):
    hourly = weather_json.get("hourly", {})
    precip = hourly.get("precipitation", [])[:hours]
    temps = hourly.get("temperature_2m", [])[:hours]
    rain_sum = float(sum(p for p in precip if p is not None))
    temp_max = float(max(temps)) if temps else 0.0
    return rain_sum, temp_max
