from django.test import SimpleTestCase


class AuthenticationRoutingTests(SimpleTestCase):
    def test_login_route_is_available(self):
        response = self.client.get("/users/login/")

        self.assertEqual(response.status_code, 200)

    def test_protected_resume_redirects_to_login(self):
        response = self.client.get("/resume/new/")

        self.assertRedirects(
            response,
            "/users/login/?next=/resume/new/",
            fetch_redirect_response=False,
        )
