from concurrent.futures import ThreadPoolExecutor
import logging

from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page

from .services import fetch_weather_forecast, fetch_weather_summary

logger = logging.getLogger(__name__)


@cache_page(300)
def weather_view(request):
    city = request.GET.get('city', 'Delhi').strip()[:80] or 'Delhi'
    with ThreadPoolExecutor(max_workers=2) as executor:
        summary_future = executor.submit(fetch_weather_summary, city)
        forecast_future = executor.submit(fetch_weather_forecast, city)
        try:
            weather_summary = summary_future.result()
        except Exception:
            logger.exception('Failed to fetch weather summary')
            weather_summary = {
                'city': city,
                'temperature': None,
                'description': _('Weather service unavailable. Please try later.'),
                'humidity': None,
                'wind_speed': None,
                'source': 'fallback',
            }
        forecast = forecast_future.result()
    return render(request, 'weather/weather.html', {
        'weather_summary': weather_summary,
        'forecast': forecast,
        'weather_ui': {
            'showHourly': _('View hourly details'),
            'hideHourly': _('Hide hourly details'),
        },
    })
