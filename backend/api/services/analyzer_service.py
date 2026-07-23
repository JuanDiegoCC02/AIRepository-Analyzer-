from api.models.repository import Repository
from api.models.analysis import Analysis

from api.serializers.repository_serializer import RepositorySerializer
from api.serializers.analysis_serializer import AnalysisSerializer

from api.utils.score_calculator import RepositoryScore
from api.utils.repository_classifier import RepositoryClassifier

from api.services.github_service import GitHubService
from api.services.activity_service import ActivityService
from api.services.documentation_service import DocumentationService
from api.services.maintainability_service import MaintainabilityService
from api.services.overall_score_service import OverallScoreService
from api.services.technologies_service import TechnologiesService
from api.services.recommendation_service import RecommendationService
from api.services.ai_summary_service import AISummaryService
from api.services.repository_insights_service import RepositoryInsightsService


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
     

# build of the metrics
     @staticmethod
     def build_metrics(repository):

        return {
            "stars": repository.stars,
            "forks": repository.forks,
            "watchers": repository.watchers,
            "open_issues": repository.open_issues,
        }
     

# build of the score
     @staticmethod
     def build_scores(analysis):

        return {
            "popularity": analysis.popularity_score,
            "activity": analysis.activity_score,
            "documentation": analysis.documentation_score,
            "maintainability": analysis.maintainability_score,
            "overall": analysis.overall_score,
        }
     

# build of the classification
     @staticmethod
     def build_classification(repository, analysis):

        return {
            "project_type": analysis.project_type,
            "main_language": repository.language,
        }
     

# build of the reponse
     @classmethod
     def build_response(
        cls,
        repository_serializer,
        analysis_serializer,
        repository,
        analysis,
        technologies,
        insights,
    ):

        return {

            "repository": repository_serializer.data,

            "analysis": analysis_serializer.data,

            "technologies": technologies,

            "metrics": cls.build_metrics(repository),

            "scores": cls.build_scores(analysis),

            "classification": cls.build_classification(
                repository,
                analysis,
            ),
            
             "insights": insights,
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

          languages = TechnologiesService.get_languages(
               repository.owner,
               repository.name
          )

          technologies = TechnologiesService.calculate_percentages(
          languages
          )

          popularity_score = RepositoryScore.popularity(
               repository.stars
          )

          category = RepositoryClassifier.classify(
              repository.name,
              repository.language,
              repository.description,
              repository.topics
          )
          
          activity_score = ActivityService.calculate(
               github_repository
          )

          documentation_score = DocumentationService.calculate(
               github_repository
          )

          maintainability_score = MaintainabilityService.calculate(
               github_repository
          )

          overall_score = OverallScoreService.calculate(
               popularity_score,
               activity_score,
               documentation_score,
               maintainability_score
          )
          
          analysis_scores = {
          "popularity_score": popularity_score,
          "activity_score": activity_score,
          "documentation_score": documentation_score,
          "maintainability_score": maintainability_score,
          "overall_score": overall_score,
          }

          insights = RepositoryInsightsService.generate(
          repository,
          analysis,
          technologies,
          )
          
          recommendations = RecommendationService.generate(
          analysis_scores
          )

          summary = AISummaryService.generate(
               github_repository,
               category,
               overall_score,
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
                    "ai_summary": summary,
                    "recommendations": "\n".join(recommendations),
               }
          )


          repository_serializer = RepositorySerializer(repository)
          analysis_serializer = AnalysisSerializer(analysis)


          return cls.build_response(
            repository_serializer,
            analysis_serializer,
            repository,
            analysis,
            technologies,
            insights,
         )
     
     