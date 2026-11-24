from unittest.mock import patch

from django.test import SimpleTestCase

from api.exceptions.github_exceptions import (
    GitHubRateLimitError,
    GitHubRequestError,
)
from api.services.technologies_service import TechnologiesService

REQUEST = "api.services.technologies_service.GitHubService.request"


class TechnologiesServiceTests(SimpleTestCase):

    def test_get_languages_returns_the_languages(self):
        with patch(REQUEST, return_value={"Python": 100}) as mock_request:
            result = TechnologiesService.get_languages("owner", "repo")

        mock_request.assert_called_once_with("/repos/owner/repo/languages")
        self.assertEqual(result, {"Python": 100})

    def test_get_languages_returns_empty_on_github_error(self):
        with patch(REQUEST, side_effect=GitHubRequestError("network")):
            result = TechnologiesService.get_languages("owner", "repo")

        self.assertEqual(result, {})

    def test_get_languages_does_not_hide_the_rate_limit(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            with self.assertRaises(GitHubRateLimitError):
                TechnologiesService.get_languages("owner", "repo")

    def test_get_languages_returns_empty_for_unexpected_data(self):
        for response in (["Python"], "text", None, 5):
            with self.subTest(response=response):
                with patch(REQUEST, return_value=response):
                    result = TechnologiesService.get_languages(
                        "owner",
                        "repo",
                    )

                self.assertEqual(result, {})
