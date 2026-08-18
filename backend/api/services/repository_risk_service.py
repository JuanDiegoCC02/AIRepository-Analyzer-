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


            
