from django.test import TestCase
from django.urls import reverse


class HomepageTests(TestCase):
    def test_homepage_shows_course_summary_and_primary_link(self):
        response = self.client.get(reverse("homepage:homepage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Алгебра по шагам")
        self.assertContains(response, "13")
        self.assertContains(
            response,
            reverse("course_management:course_index"),
        )

    def test_catalog_and_about_pages_use_live_course_counts(self):
        catalog_response = self.client.get(reverse("homepage:courses"))
        about_response = self.client.get(reverse("homepage:about"))

        self.assertEqual(catalog_response.status_code, 200)
        self.assertContains(catalog_response, "Пособие по алгебре")
        self.assertContains(catalog_response, "81")
        self.assertEqual(about_response.status_code, 200)
        self.assertContains(about_response, "13")
        self.assertContains(about_response, "81")
