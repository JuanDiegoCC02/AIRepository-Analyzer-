from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import exception_handler

from api.exceptions.api_exception_handler import custom_exception_handler
from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    GitHubServiceError,
    InvalidRepositoryURLError,
)


class GitHubExceptionHandlerTests(SimpleTestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        request = self.factory.post("/api/analyze/")
        self.context = {
            "request": request,
            "view": None,
            "args": (),
            "kwargs": {},
        }

    def test_not_found_returns_404(self):
        response = custom_exception_handler(
            GitHubNotFoundError("private internal detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "github_repository_not_found",
        )
        self.assertNotIn(
            "private internal detail",
            str(response.data),
        )

    def test_rate_limit_returns_503(self):
        response = custom_exception_handler(
            GitHubRateLimitError("internal rate-limit detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "github_rate_limit_exceeded",
        )

    def test_authentication_error_returns_502(self):
        response = custom_exception_handler(
            GitHubAuthenticationError("internal authentication detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "github_upstream_access_error",
        )

    def test_request_error_returns_502(self):
        response = custom_exception_handler(
            GitHubRequestError("internal request detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "github_request_failed",
        )

    def test_validation_error_uses_default_drf_handler(self):
        exc = ValidationError(
            {"repository_url": ["This field is required."]}
        )

        response = custom_exception_handler(exc, self.context)
        expected_response = exception_handler(exc, self.context)

        self.assertIsNotNone(response)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data,
            expected_response.data,
        )

    def test_rate_limit_with_delay_adds_retry_after(self):
        response = custom_exception_handler(
            GitHubRateLimitError("internal detail", retry_after=120),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(response["Retry-After"], "120")
        self.assertEqual(
            response.data["error"]["retry_after_seconds"],
            120,
        )
        self.assertNotIn("internal detail", str(response.data))

    def test_rate_limit_without_a_valid_delay_has_no_retry_after(self):
        for value in (None, 0, -5, "30", True, 1.5):
            with self.subTest(retry_after=value):
                response = custom_exception_handler(
                    GitHubRateLimitError("limit", retry_after=value),
                    self.context,
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )
                self.assertNotIn("Retry-After", response)
                self.assertNotIn(
                    "retry_after_seconds",
                    response.data["error"],
                )

    def test_other_github_errors_have_no_retry_after(self):
        response = custom_exception_handler(
            GitHubRequestError("network"),
            self.context,
        )

        self.assertNotIn("Retry-After", response)

    def test_unknown_github_error_returns_502(self):
        response = custom_exception_handler(
            GitHubServiceError("internal detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "github_service_error",
        )
        self.assertNotIn("internal detail", str(response.data))

    def test_invalid_repository_url_returns_400(self):
        response = custom_exception_handler(
            InvalidRepositoryURLError("internal detail"),
            self.context,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data["error"]["code"],
            "invalid_repository_url",
        )
        self.assertNotIn("internal detail", str(response.data))

    def test_unexpected_exceptions_are_not_handled_here(self):
        response = custom_exception_handler(
            RuntimeError("bug"),
            self.context,
        )

        self.assertIsNone(response)


class NotFoundRepositoryUrlTests(SimpleTestCase):

    def handle(self, repository_url):
        request = APIRequestFactory().post("/api/compare/")
        context = {"request": request, "view": None, "args": (), "kwargs": {}}

        return custom_exception_handler(
            GitHubNotFoundError("detail", repository_url=repository_url),
            context,
        )

    def test_a_safe_repository_url_is_included(self):
        response = self.handle("https://github.com/owner/repo")

        self.assertEqual(
            response.data["error"]["repository_url"],
            "https://github.com/owner/repo",
        )

    def test_unsafe_values_are_never_echoed(self):
        for value in (
            "https://evil.example/owner/repo",
            "https://github.com/owner/repo\nInjected: header",
            "https://github.com/owner/repo/extra",
            "<script>alert(1)</script>",
            None,
            123,
        ):
            with self.subTest(value=value):
                response = self.handle(value)

                self.assertNotIn("repository_url", response.data["error"])
