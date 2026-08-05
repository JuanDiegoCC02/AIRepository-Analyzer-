from datetime import datetime, time 
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
