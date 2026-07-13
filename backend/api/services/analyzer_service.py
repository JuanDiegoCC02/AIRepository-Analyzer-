from api.services.github_service import GitHubService
from api.serializers import RepositorySerializer, AnalysisSerializer
from api.models import Repository, Analysis
from api.utils.score_calculator import RepositoryScore
from api.utils.repository_classifier import RepositoryClassifier
from api.services.activity_service import ActivityService
from api.services.documentation_service import DocumentationService
from api.services.maintainability_service import MaintainabilityService
from api.services.overall_score_service import OverallScoreService


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

          popularity_score = RepositoryScore.popularity(
               repository.stars
          )

          score = RepositoryScore.popularity(repository.stars)

          category = RepositoryClassifier.classify(
              repository.name,
              repository.language,
              repository.description,
              repository.topics
          )
          
          activity_score - ActivityService.calculate(
               repository.github_updated_at
          )

          documentation_score = DocumentationService.calculate(...)

          maintainability_score = MaintainabilityService.calculate(...)

          overall_score = OverallScoreService.calculate(
               popularity_score,
               activity_score,
               documentation_score,
               maintainability_score
          )
          
          analysis, created = Analysis.objects.update_or_create(
               repository=repository,
               defaults={
                    "project_type": category,
                    "popularity_score": popularity_score,
                    "activity_score": activity_score,
                    "documentation_score": documentation_score,
                    "maintainability_score": maintainability_score,
                    "overall_score": overall_score,
                    "ai_summary": "",
                    "recommendations": "",
               }
          )

          

          activity = ActivityService.calculate(
               repository.github_updated_at
          )

          repository_serializer = RepositorySerializer(repository)
          analysis_serializer = AnalysisSerializer(analysis)

          activity_score = activity
          

          return {
               "repository": repository_serializer.data,
               "analysis": analysis_serializer.data,
          }