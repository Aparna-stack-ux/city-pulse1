from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardNavigationTests(TestCase):
	@patch("dashboard.views.fetch_weather_summary", return_value={})
	def test_dashboard_shows_ussd_link(self, fetch_weather_summary):
		user = get_user_model().objects.create_user(username="dashboard-user")
		self.client.force_login(user)

		response = self.client.get(reverse("dashboard"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'href="{reverse("ussd_simulator")}"')
		self.assertContains(response, ">USSD</a>")
		self.assertNotContains(response, 'class="bi bi-phone"')
