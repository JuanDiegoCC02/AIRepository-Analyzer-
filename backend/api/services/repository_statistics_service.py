


class RepositoryStatisticsService:

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