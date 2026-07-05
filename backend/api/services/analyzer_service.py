from api.services.github_service import GitHubService
from api.serializers import RepositorySerializer


class AnalyzerService: 

     @staticmethod
     def analyze_repository(repository_url):
          github_repository = GitHubService.get_repository(repository_url):

          repository_data = {
               
               "github_id": github_repository["id"],

               "owner": github_repository["owner"]["login"],

               "name": github_repository["name"],

               "full_name": github_repository["full_name"],

               "description": github_repository["description"],

               "html_url": github_repository["html_url"],

               "language": github_repository["language"],

               "license": (github_repository["license"]["name"] 
                           if github_repository["license"]
                           else None
                           ),

                "default_branch": github_repository["default_branch"],

                "stars": github_repository["stargazers_count"],

                "forks": github_repository["forks_count"],

                "watchers": github_repository["watchers_count"],

                "open_issues": github_repository["open_issues_count"],

                "github_created_at": github_repository["created_at"],

                "github_updated_at": github_repository["updated_at"],


          }

          serializer = RepositorySerializer(data=repository_data)

          serializer.is_valid(raise_exception=True)

          serializer.save()

          return serializer.data