from datetime import datetime, timezone 
from api.services.github_service import GitHubService 

class ReleaseAnalysisService:

    """
    Service responsible for retrieving and analyzing GitHub repository releases.
    """

    @classmethod
    def get_releases(cls, owner, repository):

        """
        Retrieves repository releases from GitHub.

        GitHub communication is delegated to GitHubService so authentication, 
        timeout and HTTP error handling remain centralized.
        """

        endpoint = (
            f"/repos/"
            f"{owner}/"
            f"{repository}/releases"
        )

        try:
            releases = GitHubService.request(endpoint)
        except Exception:
            return[]

        if not isinstance(releases, list):
            return []

        return releases


    @staticmethod
    def days_since_release(date_string):

        """
        Calculates the number of days elapsed
        since a release was published.
        """

        if not date_string:
            return None
        
        try:
            published = datetime.strptime(
                date_string,
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except ValueError:
            return None
        
        published = published.replace( tzinfo=timezone.utc)

        today = datetime.now(timezone.utc)

        return (today - published).days


    @staticmethod
    def release_status(days):

        """
        Classifies repository release activity according to the age of the latest release.
        """ 

        if days is None:
            return "Unknown"

        if days <= 30:
            return "Very Active"
        
        if days <= 90:
            return "Active"
        
        if days <= 180:
            return "Moderate"
        
        if days <= 365:
            return "Low Activity"
        
        return "Inactive"


    @staticmethod
    def stability(total_releases):

        """
        Provides a simple stability classification based on the amount of release history
        available.

        This is an indicative metric and does not represent software stability in the strict
        engineering sense.
        """

        if total_releases == 0:
            return "Unknown"

        if total_releases >= 50:
            return "Highly Established"

        if total_releases >= 20:
            return "Established"

        if total_releases >= 10:
            return "Stable"

        if total_releases >= 5:
            return "Developing"

        return "Limited History"
    

    @classmethod
    def summarize(cls, releases):

        """
        Generates a structured summary of repository releases.
        """

        if not releases: 
            return{
                "total_releases": 0,

                "published_at": None,

                "latest_release": None,

                "days_since_release": None,

                "release_status": "No Releases",

                "stability": "Unknown",
            }

        valid_releases = [
            release
            for release in releases
            if isinstance(
                release,
                dict
            )
        ]

        if not valid_releases:
            return{
                "total_releases": 0,

                "published_at": None,

                "latest_release": None,

                "days_since_release": None,

                "release_status": "No Releases",

                "stability": "Unknown",
            }

        published_releases = [
            release
            for release in valid_releases
            if release.get("published_at")
        ]

        if not published_releases:
            return {
                "total_releases": len(valid_releases),

                "latest_releases": None,

                "days_since_release": None,

                "release_status": "Unknown",

                "stability": cls.stability(len(valid_releases)),
            }

        latest =  max(
            published_releases,

            key=lambda release: release.get(
                "published_at",
                "",
            ),
        )

        days = cls.days_since_release( latest["published_at"])



        return {
            "total_releases": len(valid_releases),

            "published_at": latest.get("published_at"),

            "latest_release": latest.get("tag_name"),

            "days_since_release": days,

            "release_status": cls.release_status(days),

            "stability": cls.stability(len(valid_releases)),
        }