from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    InvalidRepositoryURLError,
)

ANALYZE = "api.views.repository_views.AnalyzerService.analyze_repository"

User = get_user_model()


class AnalyzeEndpointErrorTests(TestCase):
    """What the API client sees when the analysis cannot be completed."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("repository-analyze")
        self.payload = {"repository_url": "https://github.com/facebook/react"}

    def post(self, error):
        with patch(ANALYZE, side_effect=error):
            return self.client.post(self.url, self.payload, format="json")

    def test_rate_limit_returns_503_with_retry_after(self):
        response = self.post(
            GitHubRateLimitError("internal detail", retry_after=45)
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(response["Retry-After"], "45")
        self.assertEqual(
            response.json()["error"],
            {
                "code": "github_rate_limit_exceeded",
                "message": (
                    "GitHub is temporarily limiting requests. "
                    "Please try again later."
                ),
                "retry_after_seconds": 45,
            },
        )

    def test_rate_limit_without_delay_has_no_retry_after_header(self):
        response = self.post(GitHubRateLimitError("limit"))

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertNotIn("Retry-After", response)

    def test_unknown_repository_returns_404(self):
        response = self.post(GitHubNotFoundError("internal detail"))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"]["code"],
            "github_repository_not_found",
        )

    def test_github_failures_return_502_without_internal_details(self):
        for error in (
            GitHubAuthenticationError("token ghp_secret rejected"),
            GitHubRequestError("timeout talking to 10.0.0.5"),
        ):
            with self.subTest(error=type(error).__name__):
                response = self.post(error)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_502_BAD_GATEWAY,
                )
                self.assertNotIn("ghp_secret", response.content.decode())
                self.assertNotIn("10.0.0.5", response.content.decode())

    def test_invalid_repository_url_returns_400(self):
        response = self.post(InvalidRepositoryURLError("internal detail"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["error"]["code"],
            "invalid_repository_url",
        )
        self.assertNotIn("internal detail", response.content.decode())

    def test_missing_url_is_rejected_before_the_analysis(self):
        with patch(ANALYZE) as mock_analyze:
            response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_analyze.assert_not_called()

    def test_url_outside_github_is_rejected_before_the_analysis(self):
        with patch(ANALYZE) as mock_analyze:
            response = self.client.post(
                self.url,
                {"repository_url": "https://example.com/facebook/react"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_analyze.assert_not_called()
