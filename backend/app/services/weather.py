import requests
from typing import Optional, Dict, Any

def parse_location(location: str) -> (str, str):
    """
    Принимает строку вида '55.75,37.61'. Возвращает (lat, lon).
    Если передан город — вызывает ошибку.
    """
    if "," in location:
        lat, lon = location.split(",")
        return lat.strip(), lon.strip()
    raise ValueError("Open-Meteo API requires coordinates in 'lat,lon' format.")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Получить текущую погоду по координатам через Open-Meteo.
    Возвращает JSON вида:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        "generationtime_ms": 0.2,
        "utc_offset_seconds": 10800,
        "timezone": "Europe/Moscow",
        "timezone_abbreviation": "MSK",
        "elevation": 156.0,
        "current_weather": {
            "temperature": 21.3,         # Температура (°C)
            "windspeed": 3.6,            # Скорость ветра (км/ч)
            "winddirection": 180,        # Направление ветра (градусы)
            "weathercode": 1,            # Код погоды (см. документацию Open-Meteo)
            "is_day": 1,                 # 1 — день, 0 — ночь
            "time": "2024-06-15T12:00"  # Время измерения
        }
    }
    """
    lat, lon = parse_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true"
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    return response.json()

def get_weather_forecast(location: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Получить почасовой прогноз погоды по координатам через Open-Meteo.
    Возвращает JSON вида:
    {
        "latitude": 55.75,
        "longitude": 37.61,
        ...
        "hourly": {
            "time": ["2024-06-15T00:00", ...],
            "temperature_2m": [17.2, ...],         # Температура по часам (°C)
            "precipitation": [0.0, ...],           # Осадки по часам (мм)
            "weathercode": [1, ...],               # Код погоды (см. документацию Open-Meteo)
            "cloudcover": [20, ...],               # Облачность (%)
            "windspeed_10m": [2.5, ...]            # Скорость ветра (км/ч)
        }
    }
    Если передан date (YYYY-MM-DD), прогноз только на этот день.
    """
    lat, lon = parse_location(location)
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,weathercode,cloudcover,windspeed_10m"
    }
    if date:
        params["start_date"] = date
        params["end_date"] = date
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    return response.json()

def weather_summary(location: str) -> Dict[str, Any]:
    """
    Returns a weather summary for the next 3 hours: current weather + short-term forecast.
    Returns JSON:
    {
        "current": { ... },  # как в get_current_weather
        "forecast": [
            {
                "time": "2024-06-15T13:00",
                "temperature": 22.1,
                "precipitation": 0.0,
                "weathercode": 1,
                "cloudcover": 10,
                "windspeed": 3.2
            },
            ...
        ]
    }
    """
    lat, lon = parse_location(location)
    # Получаем текущую погоду
    current = get_current_weather(location).get("current_weather", {})
    # Получаем прогноз на ближайшие 3 часа
    import datetime
    now = datetime.datetime.utcnow()
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,weathercode,cloudcover,windspeed_10m",
        "start_date": now.strftime("%Y-%m-%d"),
        "end_date": now.strftime("%Y-%m-%d")
    }
    response = requests.get(OPEN_METEO_URL, params=params)
    response.raise_for_status()
    data = response.json()
    forecast = []
    times = data.get("hourly", {}).get("time", [])
    for i, t in enumerate(times):
        t_dt = datetime.datetime.fromisoformat(t)
        if now <= t_dt <= now + datetime.timedelta(hours=3):
            forecast.append({
                "time": t,
                "temperature": data["hourly"]["temperature_2m"][i],
                "precipitation": data["hourly"]["precipitation"][i],
                "weathercode": data["hourly"]["weathercode"][i],
                "cloudcover": data["hourly"]["cloudcover"][i],
                "windspeed": data["hourly"]["windspeed_10m"][i]
            })
    return {"current": current, "forecast": forecast}
