from api.utils.score_calculator import RepositoryScore

from api.services.activity_service import ActivityService
from api.services.documentation_service import DocumentationService
from api.services.maintainability_service import MaintainabilityService
from api.services.code_quality_service import CodeQualityService
from api.services.community_service import CommunityService
from api.services.overall_score_service import OverallScoreService


class AnalysisScoreService:

    @staticmethod
    def normalize_score(score):
        "Ensures that a score is always a valid numberbetween 0 and 100"

        if score is None:
            return 0
        try:
            score = float(score)
        except (TypeError, ValueError):
            return 0

        return max(0, min(100, score))

    @staticmethod
    def get_score_level(overall_score):
        "Converts the overall score into a human-readable quality level"

        if overall_score >= 90:
            return "Excellent"
        if overall_score >= 75:
            return "Good"
        if overall_score >= 50:
            return "Average"

        return "Needs Improvement"

    @classmethod
    def calculate_scores(
        cls,
        repository,
        github_repository,
    ):
        "Calculates all repository analysis scores and returns a normalized result"

        # Popularity
        popularity_score = RepositoryScore.popularity(
            repository.stars
        )

        # Activity
        activity_score = ActivityService.calculate(
            github_repository
        )

        # Documentation
        documentation_score = DocumentationService.calculate(
            github_repository
        )

        # Maintainability
        maintainability_score = MaintainabilityService.calculate(
            github_repository
        )

        # Code quality
        code_quality_score = CodeQualityService.calculate(
            github_repository
        )

        # Community
        community_score = CommunityService.calculate(
            github_repository
        )

        # Normalize individual scores
        popularity_score = cls.normalize_score(
            popularity_score
        )

        activity_score = cls.normalize_score(
            activity_score
        )

        documentation_score = cls.normalize_score(
            documentation_score
        )

        maintainability_score = cls.normalize_score(
            maintainability_score
        )

        code_quality_score = cls.normalize_score(
            code_quality_score
        )

        community_score = cls.normalize_score(
            community_score
        )

        # Calculate overall score
        overall_score = OverallScoreService.calculate(
            popularity_score,
            activity_score,
            documentation_score,
            maintainability_score,
            code_quality_score,
            community_score,
        )

        overall_score = cls.normalize_score(
            overall_score
        )

        # Determine quality level
        level = cls.get_score_level(
            overall_score
        )

        return {
            "popularity_score": popularity_score,

            "activity_score": activity_score,

            "documentation_score": documentation_score,

            "maintainability_score": maintainability_score,

            "code_quality_score": code_quality_score,

            "community_score": community_score,

            "overall_score": overall_score,

            "level": level,
        }