import logging

from api.models.repository import Repository
from django.db import transaction

from api.serializers.analysis_serializer import AnalysisSerializer
from api.serializers.repository_serializer import RepositorySerializer

from api.utils.repository_classifier import RepositoryClassifier

from api.services.ai_summary_service import AISummaryService
from api.services.analysis_evaluation_service import AnalysisEvaluationService
from api.services.analysis_persistence_service import AnalysisPersistenceService
from api.services.analysis_result_service import AnalysisResultService
from api.services.analysis_score_service import AnalysisScoreService
from api.services.code_quality_service import CodeQualityService
from api.services.commits_service import CommitsService
from api.services.contributors_service import ContributorsService
from api.services.github_service import GitHubService
from api.services.maintainability_service import MaintainabilityService
from api.services.readme_service import ReadmeService
from api.services.recommendation_service import RecommendationService
from api.services.release_analysis_service import ReleaseAnalysisService
from api.services.resources_cache_service import ResourcesCacheService
from api.services.repository_health_service import RepositoryHealthService
from api.services.repository_insights_service import RepositoryInsightsService
from api.services.repository_maturity_service import RepositoryMaturityService
from api.services.repository_statistics_service import RepositoryStatisticsService
from api.services.repository_structure_service import RepositoryStructureService
from api.services.repository_topics_service import RepositoryTopicsService
from api.services.technologies_service import TechnologiesService


logger = logging.getLogger(__name__)

class AnalyzerService:

    @staticmethod
    def format_repository_data(repository):

        owner = repository["owner"]["login"]
        name = repository["name"]

        license_data = repository.get("license")

        license_name = (
            license_data.get("name")
            if isinstance(license_data, dict)
            else None
        )

        return {
            "github_id": repository["id"],
            "owner": owner,
            "name": name,
            "full_name": f"{owner}/{name}",
            "description": repository.get("description"),
            "html_url": f"https://github.com/{owner}/{name}",
            "topics": repository.get("topics", []),
            "language": repository.get("language"),
            "license_name": license_name,
            "default_branch": repository.get("default_branch"),
            "stars": repository.get("stargazers_count"),
            "forks": repository.get("forks_count"),
            "watchers": repository.get("subscribers_count") or 0,
            "open_issues": repository.get("open_issues_count"),
            "github_created_at": repository["created_at"],
            "github_updated_at": repository["updated_at"],
        }


    @staticmethod
    def fetch_remote_resources(repository):
        """
        About 8 requests. Rate limits are not handled here: they stop the
        analysis, so incomplete data is never saved as a real analysis.
        """

        technology_analysis = TechnologiesService.analyze(
            repository.owner,
            repository.name,
        )

        readme_analysis = ReadmeService.load_analysis(
            repository.owner,
            repository.name,
        )

        contributors = ContributorsService.get_contributors(
            repository.owner,
            repository.name,
        )

        contributors_summary = ContributorsService.summarize(
            contributors
        )

        releases_summary = ReleaseAnalysisService.analyze(
            repository.owner,
            repository.name,
        )

        commits_summary = CommitsService.analyze(
            repository.owner,
            repository.name,
        )

        structure = RepositoryStructureService.analyze(
            repository.owner,
            repository.name,
        )

        return {
            "technologies": technology_analysis,
            "readme": readme_analysis,
            "contributors": contributors_summary,
            "releases": releases_summary,
            "commits": commits_summary,
            "structure": structure,
        }


    @classmethod
    def load_external_resources(
        cls,
        repository,
        github_repository
    ):

        pushed_at = github_repository.get("pushed_at")

        remote = ResourcesCacheService.get(
            repository.github_id,
            pushed_at,
        )

        if remote is None:
            remote = cls.fetch_remote_resources(repository)

            ResourcesCacheService.set(
                repository.github_id,
                pushed_at,
                remote,
            )

        # These only use data that is already in memory: always fresh.
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
            github_repository,
            commit_stats=remote["commits"],
        )

        return {
            "technologies": remote["technologies"],
            "readme": remote["readme"],
            "contributors": remote["contributors"],
            "statistics": statistics,
            "topics": topics,
            "maturity": maturity,
            "releases": remote["releases"],
            "commits": remote["commits"],
            "structure": remote["structure"],
        }


    @staticmethod
    def build_data_quality(resources):
        missing = sorted(
            name
            for name in ("commits", "structure", "readme")
            if isinstance(resources.get(name), dict)
            and resources[name].get("available") is False
        )

        return {
            "complete": not missing,
            "missing": missing,
        }


    @staticmethod
    def generate_summary(
        github_repository,
        category,
        technologies,
        analysis_scores,
        evaluation,
    ):
        """
        Build the analysis summary. It never raises: the summary is an
        extra, so a failure must not cost the user the whole analysis.
        """

        try:
            return AISummaryService.generate(
                github_repository,
                category,
                technologies,
                analysis_scores,
                evaluation,
            ) or ""

        except Exception:
            logger.exception("The analysis summary could not be generated.")
            return ""


    @staticmethod
    def build_classification(repository, analysis):

        return {
            "project_type": analysis.project_type,
            "main_language": repository.language,
            "license": repository.license_name,
            "owner": repository.owner,
        }

    
    @classmethod
    def build_response(
        cls,
        repository_serializer,
        analysis_serializer,
        repository,
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
        evaluation,
        recommendations,
        commits=None,
        code_quality_signals=None,
        maintainability_signals=None,
        data_quality=None,
    ):

        return {
            "repository": repository_serializer.data,
            "analysis": analysis_serializer.data,
            "analysis_result": analysis_result,
            "technologies": technology_analysis,
            "topics": topics,
            "statistics": statistics,
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
            "commits": commits,
            "code_quality_signals": code_quality_signals,
            "maintainability_signals": maintainability_signals,
            "data_quality": data_quality,
            "evaluation": evaluation,
            "recommendations": recommendations,
        }


    @classmethod
    def analyze_repository(cls, repository_url, user=None):

        github_repository = GitHubService.get_repository(
            repository_url
        )

        repository_data = cls.format_repository_data(
            github_repository
        )

        repository, _ = Repository.objects.update_or_create(
            github_id=repository_data["github_id"],
            defaults=repository_data
        )

        resources = cls.load_external_resources(
            repository,
            github_repository
        )

        technology_analysis = resources["technologies"]

        technologies = technology_analysis.get(
            "languages",
            []
        )


        statistics = resources["statistics"]

        contributors_summary = resources["contributors"]

        readme_analysis = resources["readme"]

        release_summary = resources["releases"]

        topics = resources["topics"]

        maturity = resources["maturity"]

        commit_stats = resources["commits"]

        structure = resources["structure"]

        category = RepositoryClassifier.classify(
            repository.name,
            repository.language,
            repository.description,
            repository.topics
        )

        analysis_scores = AnalysisScoreService.calculate_scores(
            repository,
            github_repository,
            commit_stats=commit_stats,
            releases=release_summary,
            readme=readme_analysis,
            structure=structure,
            contributors=contributors_summary,
        )

        code_quality_signals = CodeQualityService.breakdown(structure)

        maintainability_signals = MaintainabilityService.breakdown(
            github_repository,
            contributors_summary,
        )

        analysis_result = AnalysisResultService.build(
            analysis_scores
        )

        health = RepositoryHealthService.generate(
            analysis_scores
        )

        with transaction.atomic():

            analysis = AnalysisPersistenceService.save_analysis(
                repository=repository,
                category=category,
                scores=analysis_scores,
                summary="",
                recommendations=[],
                user=user,
            )

            evaluation = AnalysisEvaluationService.generate(
                repository,
                analysis,
            )

            recommendations = RecommendationService.generate(
                analysis_scores,
                evaluation,
            )

            insights = RepositoryInsightsService.generate(
                repository,
                analysis,
                technologies,
                evaluation,
            )

            analysis.recommendations = "\n".join(
                recommendations
            )

            analysis.save(
                update_fields=["recommendations"]
            )

        summary = cls.generate_summary(
            github_repository,
            category,
            technologies,
            analysis_scores,
            evaluation,
        )

        if summary:
            analysis.ai_summary = summary

            analysis.save(
                update_fields=["ai_summary"]
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
            recommendations,
            commits=commit_stats,
            code_quality_signals=code_quality_signals,
            maintainability_signals=maintainability_signals,
            data_quality=cls.build_data_quality(resources),
        )