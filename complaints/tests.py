from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Complaint


class ComplaintViewsTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="citizen",
			password="test-password",
		)
		self.client.force_login(self.user)

	def create_complaint(self, user, **overrides):
		fields = {
			"user": user,
			"title": "Pothole on Main Street",
			"description": "A large pothole needs repair.",
			"category": "road",
			"priority": "medium",
			"ward_number": "4",
			"location": "Main Street",
		}
		fields.update(overrides)
		return Complaint.objects.create(**fields)

	def test_create_assigns_current_user_and_redirects_to_detail(self):
		response = self.client.post(
			reverse("complaint_create"),
			{
				"title": "Pothole on Main Street",
				"description": "A large pothole needs repair.",
				"category": "road",
				"priority": "medium",
				"ward_number": "4",
				"location": "Main Street",
			},
		)

		complaint = Complaint.objects.get()
		self.assertEqual(complaint.user, self.user)
		self.assertEqual(complaint.source, "WEB")
		self.assertRedirects(
			response,
			reverse("complaint_detail", args=[complaint.pk]),
		)

	def test_list_only_shows_current_users_complaints(self):
		own_complaint = self.create_complaint(self.user)
		other_user = get_user_model().objects.create_user(username="another")
		other_complaint = self.create_complaint(
			other_user,
			title="Other user's report",
		)

		response = self.client.get(reverse("complaint_list"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(list(response.context["complaints"]), [own_complaint])
		self.assertNotContains(response, other_complaint.title)

	def test_detail_hides_another_users_complaint(self):
		other_user = get_user_model().objects.create_user(username="another")
		complaint = self.create_complaint(other_user)

		response = self.client.get(
			reverse("complaint_detail", args=[complaint.pk]),
		)

		self.assertEqual(response.status_code, 404)
