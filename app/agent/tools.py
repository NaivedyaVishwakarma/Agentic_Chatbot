# import re
# from datetime import datetime
# from urllib.parse import quote
# from zoneinfo import ZoneInfo

# import requests
# from langchain.tools import tool


# @tool
# def calculator(expression: str) -> str:
#     """Calculate basic arithmetic expressions using numbers, parentheses, and + - * / % **."""
#     expression = expression.strip().replace('^', '**')
#     if not expression or len(expression) > 100:
#         return 'Error: expression is empty or too long.'
#     if not re.fullmatch(r'[0-9\s+\-*/%().]+', expression):
#         return 'Error: only basic arithmetic characters are allowed.'
#     try:
#         result = eval(expression, {'__builtins__': {}}, {})
#     except ZeroDivisionError:
#         return 'Error: division by zero is not allowed.'
#     except Exception as exc:
#         return f'Error: could not calculate expression ({exc}).'
#     return str(result)


# @tool
# def get_current_time(timezone: str = 'Asia/Kolkata') -> str:
#     """Return the current date and time for a valid IANA time-zone such as Asia/Kolkata."""
#     try:
#         now = datetime.now(ZoneInfo(timezone))
#     except Exception as exc:
#         raise ValueError(
#             'Invalid timezone. Use an IANA timezone such as Asia/Kolkata or America/New_York.'
#         ) from exc
#     return now.strftime('%Y-%m-%d %H:%M:%S %Z')


# @tool
# def get_weather(city: str) -> str:
#     """Return current weather for a city using the public Open-Meteo geocoding and weather APIs."""
#     city = city.strip()
#     if not city:
#         raise ValueError('City name is required.')

#     geocode_url = (
#         'https://geocoding-api.open-meteo.com/v1/search'
#         f'?name={quote(city)}&count=1&language=en&format=json'
#     )
#     geocode_response = requests.get(geocode_url, timeout=10)
#     geocode_response.raise_for_status()
#     geocode_data = geocode_response.json()

#     results = geocode_data.get('results') or []
#     if not results:
#         return f'No location was found for {city}.'

#     location = results[0]
#     latitude = location['latitude']
#     longitude = location['longitude']
#     resolved_name = location.get('name', city)
#     country = location.get('country', '')

#     weather_url = (
#         'https://api.open-meteo.com/v1/forecast'
#         f'?latitude={latitude}&longitude={longitude}'
#         '&current=temperature_2m,relative_humidity_2m,wind_speed_10m'
#         '&timezone=auto'
#     )
#     weather_response = requests.get(weather_url, timeout=10)
#     weather_response.raise_for_status()
#     weather_data = weather_response.json()

#     current = weather_data['current']
#     units = weather_data.get('current_units', {})

#     return (
#         f'Current weather in {resolved_name}, {country}: '
#         f"temperature {current.get('temperature_2m')} {units.get('temperature_2m', '°C')}, "
#         f"humidity {current.get('relative_humidity_2m')} {units.get('relative_humidity_2m', '%')}, "
#         f"wind speed {current.get('wind_speed_10m')} {units.get('wind_speed_10m', 'km/h')}."
#     )


# TOOLS = [calculator, get_current_time, get_weather]


import re

from datetime import datetime

from urllib.parse import quote

from zoneinfo import ZoneInfo

import requests

from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """Calculate basic arithmetic expressions using numbers, parentheses, and + - * / % **."""
    expression = expression.strip().replace('^', '**')
    if not expression or len(expression) > 100:
        return 'Error: expression is empty or too long.'
    if not re.fullmatch(r'[0-9\s+*\-*/%().]+', expression):
        return 'Error: only basic arithmetic characters are allowed.'
    try:
        result = eval(expression, {'__builtins__': {}}, {})
    except ZeroDivisionError:
        return 'Error: division by zero is not allowed.'
    except Exception as exc:
        return f'Error: could not calculate expression ({exc}).'
    return str(result)


@tool
def get_current_time(timezone: str = 'Asia/Kolkata') -> str:
    """Return the current date and time for a valid IANA time-zone such as Asia/Kolkata."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception as exc:
        raise ValueError(
            'Invalid timezone. Use an IANA timezone such as Asia/Kolkata or America/New_York.'
        ) from exc
    return now.strftime('%Y-%m-%d %H:%M:%S %Z')


@tool
def get_weather(city: str) -> str:
    # """Return current weather for a city using the public Open-Meteo geocoding and weather APIs."""
    """Return current weather and hourly weather forecast, including rain probability, for a city using the public Open-Meteo geocoding and weather APIs."""

    city = city.strip()
    if not city:
        raise ValueError('City name is required.')

    geocode_url = (
        'https://geocoding-api.open-meteo.com/v1/search'
        f'?name={quote(city)}&count=1&language=en&format=json'
    )

    geocode_response = requests.get(geocode_url, timeout=10)
    geocode_response.raise_for_status()
    geocode_data = geocode_response.json()

    results = geocode_data.get('results') or []
    if not results:
        return f'No location was found for {city}.'

    location = results[0]
    latitude = location['latitude']
    longitude = location['longitude']
    resolved_name = location.get('name', city)
    country = location.get('country', '')

    weather_url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={latitude}&longitude={longitude}'
        '&current=temperature_2m,relative_humidity_2m,wind_speed_10m'
        '&hourly=precipitation_probability,precipitation'
        '&forecast_days=2'
        '&timezone=auto'
    )

    weather_response = requests.get(weather_url, timeout=10)
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    current = weather_data['current']
    units = weather_data.get('current_units', {})

    # Added: hourly rain data
    hourly = weather_data['hourly']
    times = hourly['time']
    rain_probability = hourly['precipitation_probability']

    # Added: rain probability after approximately 3 hours
    current_time = datetime.fromisoformat(current['time'])
    target_time = current_time.replace(minute=0, second=0, microsecond=0)
    target_3h = target_time.timestamp() + 3 * 3600

    closest_index = min(
        range(len(times)),
        key=lambda i: abs(
            datetime.fromisoformat(times[i]).timestamp() - target_3h
        )
    )

    probability_3h = rain_probability[closest_index]

    # Added: maximum rain probability tomorrow
    tomorrow = current_time.date().toordinal() + 1

    tomorrow_probabilities = [
        rain_probability[i]
        for i, time in enumerate(times)
        if datetime.fromisoformat(time).date().toordinal() == tomorrow
    ]

    tomorrow_probability = (
        max(tomorrow_probabilities)
        if tomorrow_probabilities
        else 'N/A'
    )

    print("===== WEATHER TOOL DEBUG =====")
    print("City:", resolved_name)
    print("Tomorrow rain probability:", tomorrow_probability)
    print("==============================")



    # return (
    #     f'Current weather in {resolved_name}, {country}: '
    #     f"temperature {current.get('temperature_2m')} {units.get('temperature_2m', '°C')}, "
    #     f"humidity {current.get('relative_humidity_2m')} {units.get('relative_humidity_2m', '%')}, "
    #     f"wind speed {current.get('wind_speed_10m')} {units.get('wind_speed_10m', 'km/h')}. "
    #     f'Chance of rain after approximately 3 hours: {probability_3h}%. '
    #     f'Maximum chance of rain tomorrow: {tomorrow_probability}%.'
    # )
    return (
    f"Current weather in {resolved_name}, {country}: "
    f"temperature {current.get('temperature_2m')} {units.get('temperature_2m', '°C')}, "
    f"humidity {current.get('relative_humidity_2m')} {units.get('relative_humidity_2m', '%')}, "
    f"wind speed {current.get('wind_speed_10m')} {units.get('wind_speed_10m', 'km/h')}. "
    f"Chance of rain after approximately 3 hours: {probability_3h}%. "
    f"Maximum chance of rain tomorrow: {tomorrow_probability}%. "
    f"[DEBUG: current_time={current_time}, hourly_points={len(times)}]"
)


TOOLS = [calculator, get_current_time, get_weather]