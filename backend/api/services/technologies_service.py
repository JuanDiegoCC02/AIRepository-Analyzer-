import request 


class TechnologiesService:
    BASE_URL = "https://api.github.com/repos"

    @classmethod
    def get_languages(cls, owner, repository):
        
        url = f"{cls.BASE_URL}/{owner}/{repository}/langueages"
        reponse = request.get(url)

        if reponse.status_code == 404:
            raise Exception("Repository languages not found.")

        if reponse.status_code != 200:
            raise Exception(
                f"GitHub API returned {reponse.status_code}"
            )
        
        return reponse.json()