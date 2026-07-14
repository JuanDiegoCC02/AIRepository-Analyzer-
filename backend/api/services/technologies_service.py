import requests


class TechnologiesService:

    BASE_URL = "https://api.github.com/repos"

    @classmethod
    def get_languages(cls, owner, repository):

        url = f"{cls.BASE_URL}/{owner}/{repository}/languages"

        print("=" * 50)
        print("URL:", url)

        response = requests.get(url)

        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        print("=" * 50)

        if response.status_code == 404:
            raise Exception("Repository languages not found.")

        if response.status_code != 200:
            raise Exception(
                f"GitHub API returned {response.status_code}"
            )

        return response.json()