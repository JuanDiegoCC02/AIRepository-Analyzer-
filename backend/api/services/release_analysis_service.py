from datetime import datetime, time, timezone 
import requests 

class ReleaseAnalysisService:

    BASE_URL = "https://api.github.com/repos"


    @classmethod
    def get_releases(cls, owner, repository):
        ulr = (
            f"{cls.BASE_URL}/"
            f"{owner}/"
            f"{repository}/releases"
        )

        reponse = requests.get(url)

        if reponse.status_code == 404:
            return ["not found"]

        if reponse.status_code != 200:
            raise Exception(
                f"Github API returned {reponse.status_code}"
            )

        return reponse.json()


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
    def realease_status(days):
        if days <= 30:
            return "Very Active"
        
        if days <= 90:
            return "Active"
        
        if days <= 180:
            return "Moderate"
        
        if days <= 365:
            return "Low Activity"
        
        return "Inactive"
    

        @classmethod
        def summarize(cls, releases):
            if not release: 
                return{
                    "total_releases": 0,
                    "published_at": None,
                    "lastest_release": None,
                    "days_since_release": None,
                    "release_status": "No Releases",
                    "stability": "Unknown",
                }

            latest = releases [0]

            days = cls.days_since_release(
                lastest["published_at"]
            )

            return {
                "total_releases": len(releases),
                "published_at": lastest["published_at"],
                "lastest_release": lastest["tag_name"],
                "days_since_release": days,
                "release_status": cls.release_status(
                    days
                ),
                "stability": cls.stability(
                    len(releases)
                ),
            }