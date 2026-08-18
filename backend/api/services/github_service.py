import os 
import requests

from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubAuthenticationError,
    GitHubRequestError,
)

class GitHubService:
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10

    @classmethod
    def get_headers(cls):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        token = os.getenv(
            "HITHUB_TOKEN"
        )

        if token:
            headers["Authorization"] = (
                f'Bearer {token}'
            )
        return headers


    @classmethod
    def request(
            cls,
            endpoint,
            params=None,
    ):

        url = ( 
            f"{cls.BASE_URL}" 
            f"{endpoint}"
        )

        try: 

            response = requests.get(
                url,
                headers=cls.get_headers(),
                params=params,
                timeout=cls.TIMEOUT,
            )

        except requests.Timeout as error:
            raise GitHubRequestError(
                "GitHub API request timed out."
            ) from error

        except requests.RequestException as error:
            raise GitHubRequestError(
                 "Unable to connect to GitHub API."
            ) from error

        if response.status_code == 404:
            raise GitHubNotFoundError(
                "GitHub resource was not found."
            )

        if response.status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub authentication failed."
            )

        if response.status_code == 403:
            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )
            if remaining == "0":
                raise GitHubRateLimitError(
                 "GitHub API rate limit exceeded."
                )
            raise GitHubAuthenticationError(
                "GitHub API access forbidden."
            )

        if response.status_code >= 400:
            raise GitHubRequestError(
                f"GitHub API returned "
                f"{response.status_code}"
            )
        return response.json()


    @classmethod
    def get_repository(
            cls,
            repository_url,
    ):

        owner, repository = (
            cls.extract_owner_repo(
                repository_url
            )
        )
        return cls.request(
            f"/repos/{owner}/{repository}"
        )


    @staticmethod
    def extract_owner_repo(
        repository_url,
    ):

        clean_url = (
            repository_url
            .rstrip("/")
        )

        parts = clean_url.split("/")

        if len(parts) < 2:
            raise ValueError(
                "Invalid GitHub repository URL."
            )

        owner = parts[-2]

        repository = parts[-1]

        return owner, repository