import requests


class ContributorsService:

    BASE_URL = "https://api.github.com/repos"

    @classmethod
    def get_contributors(cls, owner, repository):

        url = (
            f"{cls.BASE_URL}/"
            f"{owner}/"
            f"{repository}/contributors"
        )

        response = requests.get(url)

        if response .status_code == 404:
            raise Exception ("Repository contributors not found")

        if response.status_code != 200:
            raise Exception(
                f"GitHub API returned {response.status_code}"
            )

        return response.json()