from api.models.repository import Repository
from api.models.analysis import Analysis

from api.serializers.repository_serializer import RepositorySerializer
from api.serializers.analysis_serializer import AnalysisSerializer

from api.utils.repository_classifier import RepositoryClassifier

from api.services.github_service import GitHubService

from api.services.technologies_service import TechnologiesService
from api.services.recommendation_service import RecommendationService
from api.services.ai_summary_service import AISummaryService
from api.services.repository_insights_service import RepositoryInsightsService

from api.services.repository_statistics_service import RepositoryStatisticsService
from api.services.contributors_service import ContributorsService
from api.services.readme_service import ReadmeService
from api.services.repository_health_service import RepositoryHealthService
from api.services.repository_topics_service import RepositoryTopicsService
from api.services.repository_maturity_service import RepositoryMaturityService
from api.services.release_analysis_service import ReleaseAnalysisService
from api.services.analysis_score_service import AnalysisScoreService
from api.services.analysis_persistence_service import AnalysisPersistenceService
from api.services.analysis_result_service import AnalysisResultService
from api.services.analysis_evaluation_service import AnalysisEvaluationService




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
     

    # build_response of the score
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

            "code_quality": analysis.code_quality_score,

            "community": analysis.community_score,

            "overall": analysis.overall_score,

            "level": level,
        }
     

    # build_response of the classification
     @staticmethod
     def build_classification(repository, analysis):

        return {
            "project_type": analysis.project_type,

            "main_language": repository.language,

            "license": repository.license_name,

            "owner": repository.owner,
        }
     

    # build_respone of the data
     @classmethod
     def build_response(
        cls,
        repository_serializer,
        analysis_serializer,
        repository,
        github_repository,
        analysis,
        analysis_result,
        technology_analysis,
        topics,
        statistics,
        insights,
        contributors,
        readme,
        health,
        maturity,
        releases,
        evaluation
    ):

        return {

            "repository": repository_serializer.data,

            "analysis": analysis_serializer.data,

            "analysis_result": analysis_result,

            "technologies": technology_analysis,

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

             "evaluation": evaluation,

        }


    # new structure for the analyzer that will help in the division of responsibilities.
     @staticmethod
     def load_external_resources(repository, github_repository):

        # technologies
        technology_analysis = TechnologiesService.analyze(
            repository.owner,
            repository.name,
        )

        # readme
        readme = ReadmeService.get_readme(
            repository.owner,
            repository.name,
        )
        readme_analysis = ReadmeService.analyze(
            readme
        )


        # contributors
        contributors = ContributorsService.get_contributors(
            repository.owner,
            repository.name,
        )
        contributors_summary = ContributorsService.summarize(
            contributors
        )


        # repository  statustucs
        statistics = RepositoryStatisticsService.generate(
            github_repository
        )


        # topics
        topics = RepositoryTopicsService.analyze(
            github_repository.get(
                "topics",
                []
            )
        )


        # repository maturity
        maturity = RepositoryMaturityService.calculate(
            github_repository
        )


        # releases
        releases = ReleaseAnalysisService.get_releases(
            repository.owner,
            repository.name,
        )

        releases_summary = ReleaseAnalysisService.summarize(
            releases
        )

        return {

            "technologies": technology_analysis,

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

        # fetch repository from GitHub
        github_repository = GitHubService.get_repository(
            repository_url
        )

        # format repository data
        repository_data = cls.format_repository_data(
            github_repository
        )

        # create or update repository
        repository, created = Repository.objects.update_or_create(
            github_id=repository_data["github_id"],
            defaults=repository_data
        )

        # load external resources
        resources = cls.load_external_resources(repository, github_repository )

        technology_analysis = resources["technologies"]
        technologies = technology_analysis["languages"]
        primary_language = technology_analysis["primary_language"]
        main_stack = technology_analysis["main_stack"]
        statistics = resources["statistics"]
        contributors_summary = resources["contributors"]
        readme_analysis = resources["readme"]
        release_summary = resources["releases"]
        topics = resources["topics"]
        maturity = resources["maturity"]


        # classify repository
        category = RepositoryClassifier.classify(
            repository.name,
            repository.language,
            repository.description,
            repository.topics
        )

        # calculate analysis scores
        analysis_scores = AnalysisScoreService.calculate_scores(
            repository,
            github_repository,
        )

        # build structured analysis result
        analysis_result = AnalysisResultService.build(
            analysis_scores
        )

        # repository health
        health = RepositoryHealthService.generate(
            analysis_scores
        )

        analysis, created = AnalysisPersistenceService.save(
            repository=repository,
            category=category,
            analysis_scores=analysis_scores,
            summary=summary,
            recommendations=recommendations,
        )

        # calculate evaluation
        evaluation = AnalysisEvaluationService.generate(
            repository,
            analysis,
        )

        # generate insights
        insights = RepositoryInsightsService.generate(
            repository,
            analysis,
            technologies,
            evaluation,
        )

        # generate recommendations
        recommendations = RecommendationService.generate(
            analysis_scores,
            evaluation
        )

        # generate AI summary
        summary = AISummaryService.generate(
            github_repository,
            category,
            technologies,
            analysis_scores,
            evaluation,
        )

        repository_serializer = RepositorySerializer(
            repository
        )

        analysis_serializer = AnalysisSerializer(
            analysis
        )

        return cls.build_response(
            repository_serializer,
            analysis_serializer,
            repository,
            github_repository,
            analysis,
            analysis_result,
            technology_analysis,
            topics,
            statistics,
            insights,
            contributors_summary,
            readme_analysis,
            health,
            maturity,
            release_summary,
            evaluation,
        )
     