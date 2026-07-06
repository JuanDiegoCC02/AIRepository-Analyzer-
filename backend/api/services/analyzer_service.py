from api.services.github_service import GitHubService
from api.serializers import RepositorySerializer


class AnalyzerService: 

     @staticmethod
     def format_repository_data(repository):

          return {
               
               "github_id": repository["id"],

               "owner": repository["owner"]["login"],

               "name": repository["name"],

               "full_name": repository["full_name"],

               "description": repository["description"],

               "html_url": repository["html_url"],

               "language": repository["language"],

               "license": (repository["license"]["name"] 
                           if repository["license"]
                           else None
                           ),

                "default_branch": repository["default_branch"],

                "stars": repository["stargazers_count"],

                "forks": repository["forks_count"],

                "watchers": repository["watchers_count"],

                "open_issues": repository["open_issues_count"],

                "github_created_at": repository["created_at"],

                "github_updated_at": repository["updated_at"],


          }

     @classmethod
     def analyze_repository(cls, repository_url):
          
          github_repository = GitHubService.get_repository(repository_url)

          repository_data = cls.format_repository_data(github_repository)
          
          serializer = RepositorySerializer(data = repository_data)

          serializer.is_valid(raise_exception=True)
     
          serializer.save()

          return serializer.data
