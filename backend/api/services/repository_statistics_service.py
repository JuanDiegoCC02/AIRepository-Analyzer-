from api.services.github_service import GitHubService


class RepositoryStatisticsService:

    """
    Servicce reponsible for generating structured statiscs for a GitHub Repository.
    """

    classmethod 
    def get_repository_data(cls, owner, repository,):

        """
        Retrieves the repository info required to generate statistics.
        GitHub communication is delegated to GitHubService.
        """

        endpoint = (
            f"/repos/" 
            f"{owner}" 
            f"{repository}"
        )

        try:
            repository_data = GitHubService.request(
                endpoint
            )
        except Exception:
            return None

        if not isinstance(
            repository_data,
            dict
        ):
            return None

        return repository_data
    

    @staticmethod
    def generate (repository):

        return{

            "repository_size": repository.get("size", 0),

            "default_branch": repository.get("default_branch"),
            
            "license":(
                repository["license"]["name"]
                if repository.get("license")
                else None
            ),

            "visibility": repository.get("visibility"),

            "has_issues": repository.get("has_issues"),

            "has_projects": repository.get("has_projects"),

            "has_wiki": repository.get("has_wiki"),

            "has_discussions": repository.get(
                "has_discussions", 
                "False,"
                ),

            "archived": repository.get("archived"),

            "disabled": repository.get("disabled"),

        }