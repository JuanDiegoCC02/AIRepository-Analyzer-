from datetime import datetime, timezone 
from api.services.github_service import GitHubService 



class ReleaseAnalysisService:

    @classmethod
    def get_releases(cls, owner, repository):

        endpoint = f"/repos/{owner}/{repository}/releases"

        try:
            releases = GitHubService.request(endpoint)

        except Exception:
            return[]

        if not isinstance(releases, list):
            return []

        return releases



    @classmethod
    def summarize(cls, releases):

        if not releases: 
            return{
                "total_releases": 0,
                "latest_release": None,
                "releases": [],
            }

        releases_summary = []

        for release in releases:
            releases_summary.append(
                {
                    "name": release.get("name"),
                    "tag_name": release.get("tag_name"),
                    "published_at": release.get("published_at"),
                    "html_url": release.get("html_url"),
                    "draft": release.get("draft", False),
                    "prerelease": release.get("prerelease", False),
                }
            )

        latest_release = releases[0] 

        return {
            "total_releases": len(releases),
            "latest_release": {
                "name": latest_release.get("name"),
                "tag_name": latest_release.get("tag_name"),
                "published_at": latest_release.get("published_at"),
                "html_url": latest_release.get("html_url"),
                "draft": latest_release.get("draft", False),
                "prerelease": latest_release.get("prerelease", False),
            },
            "releases": releases_summary,
        }



    @classmethod
    def analyze(cls, owner, repository):
        releases = cls.get_releases(owner, repository)

        return cls.summarize(releases)