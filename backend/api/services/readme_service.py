import base64

from api.services.github_service import GitHubService

class ReadmeService:

    @classmethod
    def get_readme(cls, owner, repository):

        """
        Retrivies the ReadMe file from a GitHub repository
        using the centralized GitHubService
        """

        endpoint = (
            f"/repos/"
            f"{owner}/"
            f"{repository}/readme"
        )

        try: 
            data = GitHubService.request(
                endpoint
            )

        except Exception: 
            return None

        content = base64.b64decode(
            data["content"]
        ).decode(
            "utf-8",
            errors = 'ignore',
        )

        return{
            "name": data["name"],
            "path": data["path"],
            "size": data["size"],
            "download_url": data.get(
                "download_url"
            ),
            "content": content,
        }


    @staticmethod
    def analyze(readme):
        """
        Analyzes ReadMe content and returns basic documentation metrics.
        """

        if readme is None:
            return {
                "exists": False,
                "size": 0, 
                "word_count": 0,
                "sections": 0,
            }

        content = readme.get("content", "")

        words = len(content.split())

        sections = sum(
            1
            for line in content.splitlines()
            if line.strip().startswith('#')
        )

        return {
            "exists": True,
            "size": readme.get("size", 0),
            "word_count": words,
            "sections": sections,
        }
