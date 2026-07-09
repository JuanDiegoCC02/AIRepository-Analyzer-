from api.services.github_service import GitHubService
from api.serializers import RepositorySerializer
from api.models import Repository
from api.utils.score_calculator import RepositoryScore
from api.utils.repository_classifier import RepositoryClassifier


class AnalyzerService: 

# formats the repository data from GitHub API response to match the Repository model fields
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

               "license_name": (repository["license"]["name"] 
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

# analyzes a GitHub repository by fetching its data, formatting it, and saving it to the database.
     @classmethod
     def analyze_repository(cls, repository_url):
          
          github_repository = GitHubService.get_repository(repository_url)

          repository_data = cls.format_repository_data(github_repository)
          
          repository, created = Repository.objects.update_or_create(
               github_id = repository_data["github_id"],
               defaults = repository_data
          )

          score = RepositoryScore.popularity(repository.stars)

          category = RepositoryClassifier.classify(
              repository.name,
              repository.language,
              repository.description,
              repository.topics

          )

          serializer = RepositorySerializer(repository)

          return {
               "repository": serializer.data,
               "analysis": {
                    "popularity_score": score,
                    "category": category,
               }
          }
