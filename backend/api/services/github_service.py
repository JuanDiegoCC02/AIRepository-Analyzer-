import requests
from urllib.parse import urlparse

class GitHubService:
    BASE_URL = "https://api.github.com/repos"

    @staticmethod
    def extract_owner_repo(repository_url):

        parsed = urlparse(repository_url)

        path = parsed.path.strip("/")

        parts = path.split("/")

        if  len(parts) < 2:
            raise ValueError("The repository URL is invalid. ")
        owner = parts[0]
        repository = parts[1]

        return owner, repository
    

    @classmethod
    def get_repository(cls, repository_url):

        owner, repository = cls.extract_owner_repo(repository_url)
            
        url = f"{cls.BASE_URL}/{owner}/{repository}"

        response = requests.get(url)

        if response.status_code == 404:
            raise Exception("Repositorio no encontrado.")

        if response.status_code != 200:
            raise Exception(
                f"GitHub API respondió con {response.status_code}"
            )

        return response.json()