from django.test import SimpleTestCase
from django.urls import reverse


class HomeRedirectTests(SimpleTestCase):
    def test_home_redirects_to_resume_list(self):
        response = self.client.get("/")

        self.assertRedirects(
            response,
            reverse("resume_list"),
            fetch_redirect_response=False,
        )
