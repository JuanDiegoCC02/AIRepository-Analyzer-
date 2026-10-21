import requests

from unittest.mock import Mock, patch
from django.test import SimpleTestCase

from api.services.github_service import GitHubService
from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
)


class GitHubServiceTests(SimpleTestCase):

    def make_response(
        self,
        status_code=200,
        json_data=None,
        headers=None,
    ):
        response = Mock()
        response.status_code = status_code
        response.headers = headers or {}
        response.json.return_value = (
            {} if json_data is None else json_data
        )
        return response

    @patch("api.services.github_service.requests.get")
    def test_request_returns_json(self, mock_get):
        mock_get.return_value = self.make_response(
            json_data={"name": "react"}
        )

        result = GitHubService.request("/repos/facebook/react")

        self.assertEqual(result, {"name": "react"})
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/facebook/react",
            headers=GitHubService.get_headers(),
            params=None,
            timeout=GitHubService.TIMEOUT,
            allow_redirects=False,
        )

    def test_extract_owner_repo_from_valid_url(self):
        result = GitHubService.extract_owner_repo(
            "https://github.com/facebook/react"
        )

        self.assertEqual(result, ("facebook", "react"))

    def test_extract_owner_repo_accepts_www_host(self):
        result = GitHubService.extract_owner_repo(
            "https://www.github.com/facebook/react/"
        )

        self.assertEqual(result, ("facebook", "react"))

    def test_extract_owner_repo_rejects_http(self):
        with self.assertRaises(ValueError):
            GitHubService.extract_owner_repo(
                "http://github.com/facebook/react"
            )

    def test_extract_owner_repo_rejects_external_domain(self):
        with self.assertRaises(ValueError):
            GitHubService.extract_owner_repo(
                "https://evil.example/facebook/react"
            )

    def test_extract_owner_repo_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            GitHubService.extract_owner_repo(
                "https://user:password@github.com/facebook/react"
            )

    def test_extract_owner_repo_rejects_query_parameters(self):
        with self.assertRaises(ValueError):
            GitHubService.extract_owner_repo(
                "https://github.com/facebook/react?token=secret"
            )

    def test_extract_owner_repo_rejects_extra_path(self):
        with self.assertRaises(ValueError):
            GitHubService.extract_owner_repo(
                "https://github.com/facebook/react/issues"
            )

    def test_request_rejects_external_endpoint(self):
        with self.assertRaises(GitHubRequestError):
            GitHubService.request(
                "https://evil.example/repos/facebook/react"
            )

    @patch("api.services.github_service.requests.get")
    def test_request_follows_trusted_redirect(self, mock_get):
        redirect_response = self.make_response(
            status_code=301,
            headers={
                "Location": (
                    "https://api.github.com/repos/facebook/react"
                )
            },
        )
        success_response = self.make_response(
            json_data={"name": "react"}
        )
        mock_get.side_effect = [
            redirect_response,
            success_response,
        ]

        result = GitHubService.request("/repos/old-owner/old-name")

        self.assertEqual(result, {"name": "react"})
        self.assertEqual(mock_get.call_count, 2)

        for call in mock_get.call_args_list:
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertEqual(
                call.kwargs["headers"],
                GitHubService.get_headers(),
            )

    @patch("api.services.github_service.requests.get")
    def test_request_rejects_untrusted_redirect(self, mock_get):
        mock_get.return_value = self.make_response(
            status_code=302,
            headers={
                "Location": "https://evil.example/collect"
            },
        )

        with self.assertRaises(GitHubRequestError):
            GitHubService.request("/repos/facebook/react")

        # The untrusted destination must never be requested.
        mock_get.assert_called_once()

    @patch("api.services.github_service.requests.get")
    def test_request_maps_http_errors(self, mock_get):
        cases = [
            (404, {}, GitHubNotFoundError),
            (401, {}, GitHubAuthenticationError),
            (403, {"X-RateLimit-Remaining": "0"}, GitHubRateLimitError),
            (403, {}, GitHubAuthenticationError),
            (429, {}, GitHubRateLimitError),
            (500, {}, GitHubRequestError),
        ]

        for status_code, headers, expected_exception in cases:
            with self.subTest(status_code=status_code, headers=headers):
                mock_get.return_value = self.make_response(
                    status_code=status_code,
                    headers=headers,
                )

                with self.assertRaises(expected_exception):
                    GitHubService.request("/repos/facebook/react")

    @patch("api.services.github_service.requests.get")
    def test_request_maps_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout("timeout")

        with self.assertRaises(GitHubRequestError):
            GitHubService.request("/repos/facebook/react")

    @patch("api.services.github_service.requests.get")
    def test_request_maps_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("connection failed")

        with self.assertRaises(GitHubRequestError):
            GitHubService.request("/repos/facebook/react")

    @patch("api.services.github_service.requests.get")
    def test_request_rejects_invalid_json(self, mock_get):
        response = self.make_response()
        response.json.side_effect = ValueError("invalid JSON")
        mock_get.return_value = response

        with self.assertRaises(GitHubRequestError):
            GitHubService.request("/repos/facebook/react")

    @patch.object(GitHubService, "request")
    def test_get_repository_uses_shared_request(self, mock_request):
        mock_request.return_value = {
            "id": 123,
            "name": "react",
            "owner": {"login": "facebook"},
        }

        result = GitHubService.get_repository(
            "https://github.com/facebook/react"
        )

        mock_request.assert_called_once_with(
            "/repos/facebook/react"
        )
        self.assertEqual(result["full_name"], "facebook/react")

    @patch.object(GitHubService, "request")
    def test_get_repository_rejects_incomplete_metadata(self, mock_request):
        mock_request.return_value = {"id": 123}

        with self.assertRaises(GitHubRequestError):
            GitHubService.get_repository(
                "https://github.com/facebook/react"
            )