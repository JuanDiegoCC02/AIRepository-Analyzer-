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
from api.services.code_quality_service import CodeQualityService
from api.services.community_service import CommunityService
from api.services.repository_statistics_service import RepositoryStatisticsService
from api.services.contributors_service import ContributorsService
from api.services.readme_service import ReadmeService
from api.services.repository_health_service import RepositoryHealthService
from api.services.repository_topics_service import RepositoryTopicsService
from api.services.repository_maturity_service import RepositoryMaturityService
from api.services.release_analysis_service import ReleaseAnalysisService




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
     def build_metrics(repository, github_repository):

        return {
            "stars": repository.stars,

            "forks": repository.forks,

            "watchers": repository.watchers,

            "open_issues": repository.open_issues,

            "default_branch": repository.default_branch,

            "size": github_repository.get("size"),

            "subscribers": github_repository.get("subscribers_count"),

            "network_count": github_repository.get("network_count"),
             
        }
     

# build of the score
     @staticmethod
     def build_scores(analysis):

        if analysis.overall_score >= 90:
            level = "Excellent"

        elif analysis.overall_score >= 75:
            level = "Good"

        elif analysis.overall_score >= 50:
            level = "Average"

        else: 
            level = "Needs Improvement"

        return {
            "popularity": analysis.popularity_score,

            "activity": analysis.activity_score,

            "documentation": analysis.documentation_score,

            "maintainability": analysis.maintainability_score,

            "overall": analysis.overall_score,

            "code_quality": analysis.code_quality_score,

            "community": analysis.community_score,

            "level": level,
        }
     

# build of the classification
     @staticmethod
     def build_classification(repository, analysis):

        return {
            "project_type": analysis.project_type,

            "main_language": repository.language,

            "license": repository.license_name,

            "owner": repository.owner,
        }
     

# build of the reponse
     @classmethod
     def build_response(
        cls,
        repository_serializer,
        analysis_serializer,
        repository,
        github_repository,
        analysis,
        technologies,
        topics,
        statistics,
        insights,
        contributors,
        readme,
        health,
        maturity,
        releases
    ):

        return {

            "repository": repository_serializer.data,

            "analysis": analysis_serializer.data,

            "technologies": technologies,

            "topics": topics,

            "statistics": statistics,

            "metrics": cls.build_metrics(
                repository,
                github_repository,
                ),

            "scores": cls.build_scores(analysis),

            "classification": cls.build_classification(
                repository,
                analysis,
            ),
            
             "insights": insights,

             "contributors": contributors,

             "readme": readme,

             "health": health,

             "maturity": maturity, 

             "releases": releases,

        }


# new structure for the analyzer that will help in the division of responsibilities.
     @staticmethod
     def load_external_resources(
            repository,
            github_repository,
        ):

            languages = TechnologiesService.get_languages(
                repository.owner,
                repository.name,
            )

            technologies = TechnologiesService.calculate_percentages(
                languages
            )

            readme = ReadmeService.get_readme(
                repository.owner,
                repository.name,
            )

            readme_analysis = ReadmeService.analyze(
                readme
            )

            contributors = ContributorsService.get_contributors(
                repository.owner,
                repository.name,
            )

            contributors_summary = ContributorsService.summarize(
                contributors
            )

            statistics = RepositoryStatisticsService.generate(
                github_repository
            )

            topics = RepositoryTopicsService.analyze(
            github_repository.get(
                "topics",
                []
             )
            )

            maturity = RepositoryMaturityService.calculate(
                github_repository
            )

            releases = ReleaseAnalysisService.get_releases(
                repository.owner,
                repository.name,
            )

            releases_summary = ReleaseAnalysisService.summarize(
                releases
            )

            return {

                "technologies": technologies,

                "readme": readme_analysis,

                "contributors": contributors_summary,

                "statistics": statistics,

                "topics": topics,

                "maturity": maturity,

                "releases": releases_summary,

        }


        # analyzes a GitHub repository by fetching its data, formatting it, and saving it to the database.
     @classmethod
     def analyze_repository(cls, repository_url):

        # 1 fetch repository from GitHub
        github_repository = GitHubService.get_repository(
            repository_url
        )

        # 2 format repository data
        repository_data = cls.format_repository_data(
            github_repository
        )

        # 3 create or update repository
        repository, created = Repository.objects.update_or_create(
            github_id=repository_data["github_id"],
            defaults=repository_data
        )

        # 4 load external resources
        resources = cls.load_external_resources(
            repository,
            github_repository,
        )

        technologies = resources["technologies"]
        statistics = resources["statistics"]
        contributors_summary = resources["contributors"]
        readme_analysis = resources["readme"]
        release_summary = resources["releases"]
        topics = resources["topics"]
        maturity = resources["maturity"]

        # 5 calculate popularity
        popularity_score = RepositoryScore.popularity(
            repository.stars
        )

        # 6 classify repository
        category = RepositoryClassifier.classify(
            repository.name,
            repository.language,
            repository.description,
            repository.topics
        )

        # 7 calculate analysis scores
        activity_score = ActivityService.calculate(
            github_repository
        )

        documentation_score = DocumentationService.calculate(
            github_repository
        )

        maintainability_score = MaintainabilityService.calculate(
            github_repository
        )

        code_quality_score = CodeQualityService.calculate(
            github_repository
        )

        community_score = CommunityService.calculate(
            github_repository
        )

        # 8 calculate overall score
        overall_score = OverallScoreService.calculate(
            popularity_score,
            activity_score,
            documentation_score,
            maintainability_score,
            code_quality_score,
            community_score,
        )

        # 9 build scores dictionary
        analysis_scores = {
            "popularity_score": popularity_score,
            "activity_score": activity_score,
            "documentation_score": documentation_score,
            "maintainability_score": maintainability_score,
            "overall_score": overall_score,
            "community_score": community_score,
            "code_quality_score": code_quality_score,
        }

        # 10 repository health
        health = RepositoryHealthService.generate(
            analysis_scores
        )

        # 11 generate recommendations
        recommendations = RecommendationService.generate(
            analysis_scores
        )

        # 12 generate AI summary
        summary = AISummaryService.generate(
            github_repository,
            category,
            technologies,
            analysis_scores,
        )

        # 13 save analysis
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
                "code_quality_score": code_quality_score,
                "community_score": community_score,
            }
        )

        # 14 generate insights
        insights = RepositoryInsightsService.generate(
            repository,
            analysis,
            technologies,
        )

        # 15 serialize database objects
        repository_serializer = RepositorySerializer(
            repository
        )

        analysis_serializer = AnalysisSerializer(
            analysis
        )

        # 16 build final API response
        return cls.build_response(
            repository_serializer,
            analysis_serializer,
            repository,
            github_repository,
            analysis,
            technologies,
            topics,
            statistics,
            insights,
            contributors_summary,
            readme_analysis,
            health,
            maturity,
            release_summary,
        )
     