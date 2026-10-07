from django.conf import settings
from django.test import Client, TestCase
from django.utils.translation import gettext, override


class ApplicationInternationalizationTests(TestCase):
    def test_homepage_uses_each_configured_language_and_direction(self):
        client = Client()
        language_codes = [code for code, _name in settings.LANGUAGES]

        for language_code in language_codes:
            with self.subTest(language=language_code):
                response = client.get(f'/{language_code}/', HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'<html lang="{language_code}"')
                expected_direction = 'rtl' if language_code == 'ur' else 'ltr'
                self.assertContains(response, f'dir="{expected_direction}"')

                with override(language_code):
                    expected_heading = gettext('Smart City.')
                self.assertContains(response, expected_heading)
                self.assertContains(response, 'தமிழ்')
                self.assertContains(response, 'অসমীয়া')
                self.assertContains(response, 'اردو')

    def test_language_switch_sets_persistent_language_cookie(self):
        response = Client().post(
            '/i18n/setlang/',
            {'language': 'ml', 'next': '/ml/'},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/ml/')
        self.assertEqual(
            response.cookies[settings.LANGUAGE_COOKIE_NAME]['max-age'],
            settings.LANGUAGE_COOKIE_AGE,
        )
