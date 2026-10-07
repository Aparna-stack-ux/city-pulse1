from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.test import TestCase
from django.urls import reverse

from .services import FORECAST_URL, fetch_weather_forecast


class WeatherForecastTests(SimpleTestCase):
	@override_settings(OPENWEATHER_API_KEY='test-key')
	@patch('weather.services.requests.get')
	def test_groups_three_hour_data_into_daily_forecasts(self, mock_get):
		mock_response = Mock()
		mock_response.json.return_value = {
			'city': {'timezone': 0},
			'list': [
				{
					'dt': 1760000400,
					'main': {'temp': 18, 'temp_min': 16, 'temp_max': 20, 'humidity': 60},
					'weather': [{'description': 'few clouds', 'icon': '02d'}],
					'wind': {'speed': 3},
					'pop': 0.1,
				},
				{
					'dt': 1760011200,
					'main': {'temp': 22, 'temp_min': 17, 'temp_max': 24, 'humidity': 50},
					'weather': [{'description': 'clear sky', 'icon': '01d'}],
					'wind': {'speed': 2},
					'pop': 0.4,
				},
				{
					'dt': 1760083200,
					'main': {'temp': 19, 'temp_min': 15, 'temp_max': 21, 'humidity': 65},
					'weather': [{'description': 'light rain', 'icon': '10d'}],
					'wind': {'speed': 4},
					'pop': 0.8,
				},
			],
		}
		mock_get.return_value = mock_response

		forecast = fetch_weather_forecast('Delhi')

		self.assertEqual(mock_get.call_args.args[0], FORECAST_URL)
		self.assertEqual(len(forecast), 2)
		self.assertEqual(forecast[0]['temp_min'], 16)
		self.assertEqual(forecast[0]['temp_max'], 24)
		self.assertEqual(forecast[0]['precipitation'], 40)
		self.assertEqual(len(forecast[0]['hourly']), 2)

	@override_settings(OPENWEATHER_API_KEY='')
	@patch('weather.services.requests.get')
	def test_returns_no_forecast_without_an_api_key(self, mock_get):
		self.assertEqual(fetch_weather_forecast('Delhi'), [])
		mock_get.assert_not_called()


class WeatherPageCacheTests(TestCase):
	def setUp(self):
		cache.clear()

	@patch('weather.views.fetch_weather_forecast', return_value=[])
	@patch('weather.views.fetch_weather_summary', return_value={
		'city': 'Delhi',
		'temperature': None,
		'description': 'Test weather',
		'humidity': None,
		'wind_speed': None,
	})
	def test_reuses_city_response_until_explicit_refresh(self, mock_summary, mock_forecast):
		url = reverse('weather')
		self.assertEqual(self.client.get(url, {'city': 'Delhi'}).status_code, 200)
		self.assertEqual(self.client.get(url, {'city': 'Delhi'}).status_code, 200)
		mock_summary.assert_called_once_with('Delhi')
		mock_forecast.assert_called_once_with('Delhi')

		self.assertEqual(self.client.get(url, {'city': 'Delhi', '_refresh': '123'}).status_code, 200)
		self.assertEqual(mock_summary.call_count, 2)
		self.assertEqual(mock_forecast.call_count, 2)
