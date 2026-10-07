import requests
from django.conf import settings
from datetime import datetime, timezone
from django.utils.translation import gettext as _
from django.utils.formats import date_format

BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'


def fetch_weather_summary(city):
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return {
            'city': city,
            'temperature': None,
            'description': _('Weather API key not configured'),
            'humidity': None,
            'wind_speed': None,
            'source': 'fallback',
        }

    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=1)
        response.raise_for_status()
        weather = response.json()
        conditions = weather['weather'][0]
        main = weather['main']
        return {
            'city': weather.get('name', city),
            'temperature': main['temp'],
            'feels_like': main.get('feels_like'),
            'temp_min': main.get('temp_min'),
            'temp_max': main.get('temp_max'),
            'pressure': main.get('pressure'),
            'description': conditions['description'].title(),
            'icon': conditions.get('icon'),
            'humidity': main['humidity'],
            'wind_speed': weather['wind']['speed'],
            'source': 'openweather',
        }
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 401:
            description = _('OpenWeather API key was rejected')
        else:
            description = _('Unable to fetch weather')
        return {
            'city': city,
            'temperature': None,
            'description': description,
            'icon': None,
            'humidity': None,
            'wind_speed': None,
            'source': 'fallback',
        }
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return {
            'city': city,
            'temperature': None,
            'description': _('Unable to fetch weather'),
            'icon': None,
            'humidity': None,
            'wind_speed': None,
            'source': 'fallback',
        }


def fetch_weather_forecast(city):
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return []

    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=1)
        response.raise_for_status()
        payload = response.json()
        timezone_offset = payload.get('city', {}).get('timezone', 0)
        daily_forecasts = {}

        for item in payload.get('list', []):
            main = item.get('main', {})
            if item.get('dt') is None or main.get('temp') is None:
                continue

            local_time = datetime.fromtimestamp(item['dt'] + timezone_offset, timezone.utc)
            day_key = local_time.date().isoformat()
            conditions = (item.get('weather') or [{}])[0]
            forecast = daily_forecasts.setdefault(day_key, {
                'date': day_key,
                'date_label': date_format(local_time, 'D, d M'),
                'temperature': main['temp'],
                'temp_min': main.get('temp_min', main['temp']),
                'temp_max': main.get('temp_max', main['temp']),
                'description': conditions.get('description', _('Conditions unavailable')).title(),
                'icon': conditions.get('icon'),
                'humidity': main.get('humidity'),
                'wind_speed': item.get('wind', {}).get('speed'),
                'precipitation': round((item.get('pop') or 0) * 100),
                'representative_hour': abs(local_time.hour - 12),
                'hourly': [],
            })

            forecast['temp_min'] = min(forecast['temp_min'], main.get('temp_min', main['temp']))
            forecast['temp_max'] = max(forecast['temp_max'], main.get('temp_max', main['temp']))
            forecast['precipitation'] = max(forecast['precipitation'], round((item.get('pop') or 0) * 100))

            if abs(local_time.hour - 12) < forecast['representative_hour']:
                forecast.update({
                    'temperature': main['temp'],
                    'description': conditions.get('description', _('Conditions unavailable')).title(),
                    'icon': conditions.get('icon'),
                    'humidity': main.get('humidity'),
                    'wind_speed': item.get('wind', {}).get('speed'),
                    'representative_hour': abs(local_time.hour - 12),
                })

            forecast['hourly'].append({
                'time': date_format(local_time, 'P'),
                'temperature': main['temp'],
                'description': conditions.get('description', _('Conditions unavailable')).title(),
                'icon': conditions.get('icon'),
            })

        forecasts = list(daily_forecasts.values())[:5]
        for forecast in forecasts:
            forecast.pop('representative_hour', None)
        return forecasts
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []
