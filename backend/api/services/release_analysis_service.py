from urllib.parse import quote
from api.services.github_service import GitHubService


class ReleaseAnalysisService:
    """Retrieves and summarizes repository releases from GitHub."""

    @classmethod
    def get_releases(cls, owner, repository):
        """Fetch releases for a GitHub repository."""
        endpoint = f"/repos/{owner}/{repository}/releases"

        try:
            releases = GitHubService.request(endpoint)
        except Exception:
            return []

        if not isinstance(releases, list):
            return []

        return [
            release
            for release in releases
            if isinstance(release, dict)
        ]

    @staticmethod
    def serialize_release(release, owner, repository):
        """Normalize a release into the API response format."""
        tag_name = release.get("tag_name")

        release_url = None

        if isinstance(tag_name, str) and tag_name.strip():
            encoded_tag = quote(tag_name, safe="")
            release_url = (
                f"https://github.com/{owner}/{repository}"
                f"/releases/tag/{encoded_tag}"
            )

        return {
            "name": release.get("name"),
            "tag_name": tag_name,
            "published_at": release.get("published_at"),
            "html_url": release_url,
            "draft": release.get("draft", False),
            "prerelease": release.get("prerelease", False),
        }

    @classmethod
    def summarize(cls, releases, owner, repository):
        """Build a summary of repository releases."""
        if not isinstance(releases, list) or not releases:
            return {
                "total_releases": 0,
                "latest_release": None,
                "releases": [],
            }

        releases_summary = [
            cls.serialize_release(release, owner, repository)
            for release in releases
            if isinstance(release, dict)
        ]

        if not releases_summary:
            return {
                "total_releases": 0,
                "latest_release": None,
                "releases": [],
            }

        return {
            "total_releases": len(releases_summary),
            "latest_release": releases_summary[0],
            "releases": releases_summary,
        }

    @classmethod
    def analyze(cls, owner, repository):
        """Fetch and summarize repository releases."""
        releases = cls.get_releases(owner, repository)

        return cls.summarize(
            releases,
            owner,
            repository,
        )
