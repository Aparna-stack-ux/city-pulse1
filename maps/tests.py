from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from complaints.models import Complaint


class MapViewTests(TestCase):
    def test_map_page_renders_with_leaflet_and_data_payload(self):
        user = get_user_model().objects.create_user(username='maria', password='StrongPass!123')
        Complaint.objects.create(
            user=user,
            title='Street light outage',
            description='A street light is not working near the station.',
            category='street_light',
            priority='high',
            ward_number='12',
            location='Central Station',
            latitude='51.5033',
            longitude='-0.1195',
        )

        response = self.client.get(reverse('map'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CityPulse live map')
        self.assertContains(response, 'leaflet-map')
        self.assertContains(response, 'map-data')
        self.assertContains(response, 'L.map(')

    def test_complaint_form_rejects_invalid_coordinates(self):
        user = get_user_model().objects.create_user(username='liam', password='StrongPass!123')
        self.client.force_login(user)

        response = self.client.post(
            reverse('complaint_create'),
            {
                'title': 'Broken road',
                'description': 'Large pothole near the school.',
                'category': 'road',
                'priority': 'medium',
                'ward_number': '4',
                'location': 'Green Park',
                'latitude': '200',
                'longitude': '-200',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'latitude',
            'Ensure this value is less than or equal to 90.',
        )
        self.assertFormError(
            response.context['form'],
            'longitude',
            'Ensure this value is greater than or equal to -180.',
        )
