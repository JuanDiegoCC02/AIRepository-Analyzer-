import requests

from unittest.mock import Mock, patch
from django.test import SimpleTestCase

from api.services.github_service import GitHubService
from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    InvalidRepositoryURLError,
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

    # --------------------------------------------------
    # Rate limit information
    # --------------------------------------------------

    def test_retry_after_header_is_used_in_seconds(self):
        result = GitHubService._retry_after_seconds({"Retry-After": "42"})

        self.assertEqual(result, 42)

    def test_reset_header_is_converted_to_seconds_from_now(self):
        result = GitHubService._retry_after_seconds(
            {"X-RateLimit-Reset": "1700000600"},
            now=1700000000,
        )

        self.assertEqual(result, 600)

    def test_retry_after_is_limited_and_never_below_one_second(self):
        too_long = GitHubService._retry_after_seconds(
            {"Retry-After": "999999"}
        )
        already_reset = GitHubService._retry_after_seconds(
            {"X-RateLimit-Reset": "1699999000"},
            now=1700000000,
        )

        self.assertEqual(too_long, GitHubService.MAX_RETRY_AFTER)
        self.assertEqual(already_reset, 1)

    def test_invalid_rate_limit_headers_return_none(self):
        for headers in (
            {},
            {"Retry-After": "soon"},
            {"Retry-After": "-5"},
            {"X-RateLimit-Reset": "tomorrow"},
            {"Retry-After": None},
            None,
        ):
            with self.subTest(headers=headers):
                self.assertIsNone(
                    GitHubService._retry_after_seconds(headers)
                )

    @patch("api.services.github_service.requests.get")
    def test_rate_limit_error_carries_the_retry_delay(self, mock_get):
        mock_get.return_value = self.make_response(
            status_code=429,
            headers={"Retry-After": "30"},
        )

        with self.assertRaises(GitHubRateLimitError) as context:
            GitHubService.request("/repos/facebook/react")

        self.assertEqual(context.exception.retry_after, 30)

    @patch("api.services.github_service.requests.get")
    def test_secondary_rate_limit_403_is_a_rate_limit(self, mock_get):
        mock_get.return_value = self.make_response(
            status_code=403,
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "10"},
        )

        with self.assertRaises(GitHubRateLimitError) as context:
            GitHubService.request("/repos/facebook/react")

        self.assertEqual(context.exception.retry_after, 60)

    @patch("api.services.github_service.requests.get")
    def test_rate_limit_without_headers_has_no_retry_delay(self, mock_get):
        mock_get.return_value = self.make_response(status_code=429)

        with self.assertRaises(GitHubRateLimitError) as context:
            GitHubService.request("/repos/facebook/react")

        self.assertIsNone(context.exception.retry_after)

    # --------------------------------------------------
    # Invalid repository URLs
    # --------------------------------------------------

    def test_invalid_repository_urls_raise_a_specific_error(self):
        invalid_urls = [
            "http://github.com/facebook/react",
            "https://example.com/facebook/react",
            "https://github.com/facebook",
            "https://github.com/facebook/react?tab=readme",
            "",
            None,
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(InvalidRepositoryURLError):
                    GitHubService.extract_owner_repo(url)

    def test_invalid_repository_url_error_is_still_a_value_error(self):
        self.assertTrue(issubclass(InvalidRepositoryURLError, ValueError))
