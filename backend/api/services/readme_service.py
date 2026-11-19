import base64
import binascii

from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
    GitHubServiceError,
)
from api.services.github_service import GitHubService


class ReadmeService:

    @classmethod
    def get_readme(cls, owner, repository):

        endpoint = (
            f"/repos/"
            f"{owner}/"
            f"{repository}/readme"
        )

        try:
            data = GitHubService.request(endpoint)

        except GitHubNotFoundError:
            return None

        if not isinstance(data, dict):
            raise GitHubRequestError("Unexpected README response.")

        encoded = data.get("content")

        if not isinstance(encoded, str):
            raise GitHubRequestError("The README has no content.")

        try:
            content = base64.b64decode(encoded).decode(
                "utf-8",
                errors="ignore",
            )
        except (binascii.Error, ValueError) as error:
            raise GitHubRequestError(
                "The README content could not be decoded."
            ) from error

        return {
            "name": data.get("name"),
            "path": data.get("path"),
            "size": data.get("size", 0),
            "download_url": data.get("download_url"),
            "content": content,
        }

    @staticmethod
    def unavailable():
        """Analysis used when the README could not be checked."""
        return {
            "available": False,
            "exists": None,
            "size": 0,
            "word_count": 0,
            "sections": 0,
        }

    @staticmethod
    def analyze(readme):
        """Analyzes README content and returns basic documentation metrics."""

        if readme is None:
            return {
                "available": True,
                "exists": False,
                "size": 0,
                "word_count": 0,
                "sections": 0,
            }

        content = readme.get("content", "")

        words = len(content.split())

        sections = sum(
            1
            for line in content.splitlines()
            if line.strip().startswith('#')
        )

        return {
            "available": True,
            "exists": True,
            "size": readme.get("size", 0),
            "word_count": words,
            "sections": sections,
        }

    @classmethod
    def load_analysis(cls, owner, repository):
        try:
            readme = cls.get_readme(owner, repository)

        except GitHubRateLimitError:
            # Partial data would be saved as a real analysis: stop instead.
            raise

        except GitHubServiceError:
            return cls.unavailable()

        return cls.analyze(readme)
