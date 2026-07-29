import base64
import requests

class ReadmeService:

    BASE_URL = "https://api.github.com/repos"

    @classmethod

    def get_readme(cls, owner, repository):
        url= (
            f"{cls.BASE_URL}/"
            f"{owner}/"
            f"{repository}/readme"
        )

        response = requests.get(url)

        if response.status_code == 404:
            return None
        
        if response.status_code != 200:
            raise Exception(
                f"GitHub API returned {response.status_code}"
            )

        data = response.json()

        content = base64.b64decode(
            data["content"]
        ).decode("utf-8", errors="ignore")

        return{
            "name": data["name"],
            "path": data["path"],
            "size": data["size"],
            "download_url": data["download_url"],
            "content": content,
        }