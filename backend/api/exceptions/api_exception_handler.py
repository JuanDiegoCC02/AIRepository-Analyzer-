import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    GitHubServiceError,
)


logger = logging.getLogger(__name__)


GITHUB_ERROR_RESPONSES = {
    GitHubNotFoundError: (
        status.HTTP_404_NOT_FOUND,
        "github_repository_not_found",
        "The requested GitHub repository was not found or is not accessible.",
    ),
    GitHubRateLimitError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "github_rate_limit_exceeded",
        "GitHub is temporarily limiting requests. Please try again later.",
    ),
    GitHubAuthenticationError: (
        status.HTTP_502_BAD_GATEWAY,
        "github_upstream_access_error",
        "GitHub could not authorize the upstream request.",
    ),
    GitHubRequestError: (
        status.HTTP_502_BAD_GATEWAY,
        "github_request_failed",
        "The request to GitHub could not be completed.",
    ),
    GitHubServiceError: (
        status.HTTP_502_BAD_GATEWAY,
        "github_service_error",
        "An error occurred while communicating with GitHub.",
    ),
}


def custom_exception_handler(exc, context):
    """
    Convert GitHub service exceptions into safe, consistent HTTP responses.

    Delegate all other exceptions to Django REST Framework's default handler.
    """

    if isinstance(exc, GitHubServiceError):
        for exception_type, error_data in GITHUB_ERROR_RESPONSES.items():
            if isinstance(exc, exception_type):
                http_status, error_code, message = error_data
                break
        else:
            http_status = status.HTTP_502_BAD_GATEWAY
            error_code = "github_service_error"
            message = "An error occurred while communicating with GitHub."

        logger.warning(
            "GitHub service exception handled: %s",
            type(exc).__name__,
        )

        return Response(
            {
                "error": {
                    "code": error_code,
                    "message": message,
                }
            },
            status=http_status,
        )

    response = exception_handler(exc, context)

    if response is None and isinstance(exc, APIException):
        logger.exception("An API exception was not handled by DRF.")

    return response