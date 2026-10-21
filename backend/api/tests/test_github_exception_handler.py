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
