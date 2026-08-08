from api.services.activity_service import ActivityService
from api.services.documentation_service import DocumentationService
from api.services.maintainability_service import MaintainabilityService
from api.services.code_quality_service import CodeQualityService
from api.services.community_service import CommunityService
from api.services.overall_score_service import OverallScoreService
from api.utils.score_calculator import RepositoryScore


class AnalysisScoreService:

    @staticmethod
    def calculate_popularity(repository):
        "Calculates the repository popularity scorebased on its GitHub stars."

        return RepositoryScore.popularity(
            repository.stars
        )

    @staticmethod
    def calculate_activity(github_repository):
        "Calculates the repository activity score using GitHub repository activity data."

        return ActivityService.calculate(
            github_repository
        )

    @staticmethod
    def calculate_documentation(github_repository):
        "Calculates the repository documentation score."

        return DocumentationService.calculate(
            github_repository
        )

    @staticmethod
    def calculate_maintainability(github_repository):
        "Calculates the repository maintainability score."

        return MaintainabilityService.calculate(
            github_repository
        )

    @staticmethod
    def calculate_code_quality(github_repository):
        "Calculates the repository code quality score."

        return CodeQualityService.calculate(
            github_repository
        )

    @staticmethod
    def calculate_community(github_repository):
        "Calculates the repository community score."

        return CommunityService.calculate(
            github_repository
        )

    @classmethod
    def calculate_scores(cls, repository, github_repository):
        "Calculates all individual repository scores and the final overall score."

        popularity_score = cls.calculate_popularity(
            repository
        )

        activity_score = cls.calculate_activity(
            github_repository
        )

        documentation_score = cls.calculate_documentation(
            github_repository
        )

        maintainability_score = cls.calculate_maintainability(
            github_repository
        )

        code_quality_score = cls.calculate_code_quality(
            github_repository
        )

        community_score = cls.calculate_community(
            github_repository
        )

        overall_score = OverallScoreService.calculate(
            popularity_score,
            activity_score,
            documentation_score,
            maintainability_score,
            code_quality_score,
            community_score,
        )

        return {
            "popularity_score": popularity_score,
            "activity_score": activity_score,
            "documentation_score": documentation_score,
            "maintainability_score": maintainability_score,
            "code_quality_score": code_quality_score,
            "community_score": community_score,
            "overall_score": overall_score,
        }