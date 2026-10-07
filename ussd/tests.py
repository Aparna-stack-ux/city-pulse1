from django.test import TestCase
from django.urls import reverse

from .models import USSDSession


class USSDFlowTests(TestCase):
	def submit(self, value):
		return self.client.post(
			reverse("ussd_simulator"),
			{"user_input": value},
		)

	def enter_main_menu(self):
		self.client.get(reverse("ussd_simulator"))
		self.submit("0712345678")

	def test_complaint_flow_records_and_tracks_report(self):
		self.enter_main_menu()
		response = self.submit("1")
		self.assertContains(response, "Enter category")

		response = self.submit("1")
		self.assertContains(response, "location of the problem")
		response = self.submit("Main Street")
		self.assertContains(response, "Describe the problem")
		response = self.submit("Large pothole")

		report = USSDSession.objects.get(current_menu="completed")
		self.assertEqual(report.data["category"], "Road")
		self.assertContains(response, f"CP-{report.pk:04d}")
		self.assertNotContains(response, "Invalid session")

		self.submit("2")
		response = self.submit(f"CP-{report.pk:04d}")
		self.assertContains(response, "Status: Received")
		self.assertContains(response, "Category: Road")

	def test_unknown_state_restarts_instead_of_showing_invalid_session(self):
		session = self.client.session
		session["ussd_state"] = "unknown"
		session.save()

		response = self.submit("anything")

		self.assertContains(response, "mobile number to restart")
		self.assertNotContains(response, "Invalid session")

	def test_phone_screen_has_country_code_and_mobile_input(self):
		response = self.client.get(reverse("ussd_simulator"))

		self.assertContains(response, 'id="country-code"')
		self.assertContains(response, 'placeholder="Enter your mobile number"')

	def test_main_menu_choices_are_tappable(self):
		self.client.get(reverse("ussd_simulator"))
		response = self.submit("0712345678")

		self.assertContains(response, 'data-response="1"')
		self.assertContains(response, 'data-response="5"')
