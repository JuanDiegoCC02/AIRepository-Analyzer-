from datetime import datetime, timezone 
import requests 

class ReleaseAnalysisService:

    BASE_URL = "https://api.github.com/repos"


    @classmethod
    def get_releases(cls, owner, repository):
        url = (
            f"{cls.BASE_URL}/"
            f"{owner}/"
            f"{repository}/releases"
        )

        response = requests.get(url)

        if response.status_code == 404:
            return ["not found"]

        if response.status_code != 200:
            raise Exception(
                f"Github API returned {response.status_code}"
            )

        return response.json()


    @staticmethod
    def days_since_release(date_string):
        published = datetime.strptime(
            date_string,
            "%Y-%m-%dT%H:%M:%SZ"
        )
        published = published.replace(
            tzinfo=timezone.utc
        )

        today = datetime.now(timezone.utc)

        return (today - published).days


    @staticmethod
    def release_status(days):
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
        if total_releases >= 100:
            return "Excellent"

        if total_releases >= 50:
            return "High"

        if total_releases >= 20:
            return "Good"

        if total_releases >= 5:
            return "Moderate"

        return "Low"
    

    @classmethod
    def summarize(cls, releases):
        if not releases: 
            return{
                "total_releases": 0,
                "published_at": None,
                "latest_release": None,
                "days_since_release": None,
                "release_status": "No Releases",
                "stability": "Unknown",
            }

        latest = releases [0]

        days = cls.days_since_release(
            latest["published_at"]
        )

        return {
            "total_releases": len(releases),
            "published_at": latest["published_at"],
            "latest_release": latest["tag_name"],
            "days_since_release": days,
            "release_status": cls.release_status(
                days
            ),
            "stability": cls.stability(
                len(releases)
            ),
        }