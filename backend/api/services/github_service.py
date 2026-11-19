import os
import time

import requests

from urllib.parse import urljoin, urlparse

from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    InvalidRepositoryURLError,
)


class GitHubService:
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10
    MAX_REDIRECTS = 3

    # Longest wait (seconds) we report to API clients after a rate limit.
    MAX_RETRY_AFTER = 3600

    REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
    ALLOWED_REPOSITORY_HOSTS = {"github.com", "www.github.com"}
    ALLOWED_API_HOST = "api.github.com"

    @classmethod
    def get_headers(cls):
        """Build the headers used for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        token = os.getenv("GITHUB_TOKEN")

        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    @classmethod
    def _validate_api_url(cls, url):
        """
        Reject API URLs that could send requests outside the trusted host.
        """
        parsed_url = urlparse(url)

        try:
            port = parsed_url.port
        except ValueError as error:
            raise GitHubRequestError(
                "GitHub API returned an invalid URL."
            ) from error

        if (
            parsed_url.scheme != "https"
            or parsed_url.hostname != cls.ALLOWED_API_HOST
            or parsed_url.username is not None
            or parsed_url.password is not None
            or port not in (None, 443)
        ):
            raise GitHubRequestError(
                "GitHub API returned an untrusted URL."
            )

        return url

    @classmethod
    def _build_api_url(cls, endpoint):
        """Build an API URL from a relative endpoint."""
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise GitHubRequestError(
                "GitHub API endpoint must be a relative path."
            )

        parsed_endpoint = urlparse(endpoint)

        if (
            parsed_endpoint.scheme
            or parsed_endpoint.netloc
            or parsed_endpoint.fragment
        ):
            raise GitHubRequestError(
                "GitHub API endpoint must be a relative path."
            )

        url = f"{cls.BASE_URL}{endpoint}"

        return cls._validate_api_url(url)

    @classmethod
    def _retry_after_seconds(cls, headers, now=None):
        """
        Seconds to wait before retrying, read from the rate limit headers.

        GitHub sends `Retry-After` (seconds) for secondary limits and
        `X-RateLimit-Reset` (epoch seconds) for the primary limit. The
        result is an integer between 1 and MAX_RETRY_AFTER, or None when
        the headers are missing or invalid.
        """
        try:
            retry_after = headers.get("Retry-After")
            reset = headers.get("X-RateLimit-Reset")
        except AttributeError:
            return None

        seconds = None

        if isinstance(retry_after, str) and retry_after.strip().isdigit():
            seconds = int(retry_after.strip())

        elif isinstance(reset, str) and reset.strip().isdigit():
            current = int(now if now is not None else time.time())
            seconds = int(reset.strip()) - current

        if seconds is None:
            return None

        return max(1, min(seconds, cls.MAX_RETRY_AFTER))

    @classmethod
    def _handle_response_error(cls, response):
        """Convert GitHub HTTP errors into application exceptions."""
        status_code = response.status_code

        if status_code == 404:
            raise GitHubNotFoundError(
                "GitHub resource was not found or is not accessible."
            )

        if status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub authentication failed."
            )

        if status_code == 429:
            raise GitHubRateLimitError(
                "GitHub API rate limit exceeded.",
                retry_after=cls._retry_after_seconds(response.headers),
            )

        if status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")

            # Secondary rate limits answer 403 with a Retry-After header.
            if remaining == "0" or response.headers.get("Retry-After"):
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded.",
                    retry_after=cls._retry_after_seconds(response.headers),
                )

            raise GitHubAuthenticationError(
                "GitHub API access was forbidden."
            )

        if status_code >= 400:
            raise GitHubRequestError(
                f"GitHub API returned HTTP {status_code}."
            )

    @classmethod
    def request(cls, endpoint, params=None):
        """
        Send a GET request to the GitHub API.

        Redirects are followed only when the destination is HTTPS on
        api.github.com. Every request disables automatic redirects so
        the destination can be validated before sending credentials.
        """
        url = cls._build_api_url(endpoint)
        request_params = params

        for redirect_count in range(cls.MAX_REDIRECTS + 1):
            try:
                response = requests.get(
                    url,
                    headers=cls.get_headers(),
                    params=request_params,
                    timeout=cls.TIMEOUT,
                    allow_redirects=False,
                )

            except requests.Timeout as error:
                raise GitHubRequestError(
                    "GitHub API request timed out."
                ) from error

            except requests.RequestException as error:
                raise GitHubRequestError(
                    "Unable to connect to GitHub API."
                ) from error

            if response.status_code in cls.REDIRECT_STATUS_CODES:
                if redirect_count >= cls.MAX_REDIRECTS:
                    raise GitHubRequestError(
                        "GitHub API exceeded the redirect limit."
                    )

                location = response.headers.get("Location")

                if not location:
                    raise GitHubRequestError(
                        "GitHub returned a redirect without a location."
                    )

                redirect_url = urljoin(url, location)
                cls._validate_api_url(redirect_url)

                url = redirect_url
                request_params = None
                continue

            if 300 <= response.status_code < 400:
                raise GitHubRequestError(
                    "GitHub API returned an unsupported redirect response."
                )

            cls._handle_response_error(response)

            try:
                return response.json()

            except ValueError as error:
                raise GitHubRequestError(
                    "GitHub API returned an invalid JSON response."
                ) from error

        raise GitHubRequestError(
            "GitHub API request could not be completed."
        )

    @classmethod
    def get_repository(cls, repository_url):
        """
        Retrieve repository metadata using the shared request method.
        """
        owner, repository = cls.extract_owner_repo(repository_url)

        data = cls.request(f"/repos/{owner}/{repository}")

        if not isinstance(data, dict):
            raise GitHubRequestError(
                "GitHub returned an unexpected repository response."
            )

        owner_data = data.get("owner")
        actual_owner = (
            owner_data.get("login")
            if isinstance(owner_data, dict)
            else None
        )
        actual_name = data.get("name")

        if not actual_owner or not actual_name:
            raise GitHubRequestError(
                "GitHub returned incomplete repository metadata."
            )

        data["full_name"] = f"{actual_owner}/{actual_name}"

        return data

    @classmethod
    def extract_owner_repo(cls, repository_url):
        """
        Extract the owner and repository from a GitHub HTTPS URL.
        """
        if not isinstance(repository_url, str) or not repository_url.strip():
            raise InvalidRepositoryURLError(
                "A valid HTTPS GitHub repository URL is required."
            )

        parsed_url = urlparse(repository_url.strip())

        try:
            port = parsed_url.port
        except ValueError as error:
            raise InvalidRepositoryURLError(
                "The GitHub repository URL contains an invalid port."
            ) from error

        hostname = parsed_url.hostname

        if (
            parsed_url.scheme != "https"
            or hostname is None
            or hostname.lower() not in cls.ALLOWED_REPOSITORY_HOSTS
            or parsed_url.username is not None
            or parsed_url.password is not None
            or port not in (None, 443)
        ):
            raise InvalidRepositoryURLError(
                "The URL must be an HTTPS GitHub repository URL."
            )

        if parsed_url.query or parsed_url.fragment:
            raise InvalidRepositoryURLError(
                "The GitHub repository URL cannot contain "
                "query parameters or fragments."
            )

        parts = parsed_url.path.strip("/").split("/")

        if (
            len(parts) != 2
            or not parts[0]
            or not parts[1]
            or "%" in parts[0]
            or "%" in parts[1]
            or parts[0] in {".", ".."}
            or parts[1] in {".", ".."}
        ):
            raise InvalidRepositoryURLError(
                "The URL must contain a GitHub owner and repository."
            )

        return parts[0], parts[1]