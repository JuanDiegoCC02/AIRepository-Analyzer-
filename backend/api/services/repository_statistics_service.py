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
    def generate (repository_data,):

        """
        Generates a normalized statistics object from GitHub repository data.
        """

        if not repository_data:
            return{
                "stars": 0,
                "forks": 0,
                "watchers": 0,
                "open_issues": 0,
                "size": 0,
                "subscribers": 0,
                "network_count": 0,
                "has_wiki": False,
                "has_page": False,
                "is_fork": False,
                "archived": False,
            }

        return{
            "stars": repository_data.get(
                "stargazers_sount",
                0
            ),

            "forks": repository_data.get(
                "forks_count",
                0
            ),

            "watchers": repository_data.get(
                "watchers_count",
                0
            ),

            "open_issues": repository_data.get(
                "open_issues_count",
                0
            ),

            "size": repository_data.get(
                "size",
                0
            ),

            "subscribers": repository_data.get(
                "subscribers_count",
                0
            ),

            "network_count": repository_data.get(
                "networks_count",
                0
            ),
            
            "has_wiki": repository_data.get(
                "has_wiki",
                False,
            ),

            "has_pages": repository_data.get(
                "has_pages",
                False
            ),

            "is_fork": repository_data.get(
                "is_fork",
                False
            ),

            "archived": repository_data.get(
                "archived",
                False
            ),
        }

    