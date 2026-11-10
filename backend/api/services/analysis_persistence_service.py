import math
from numbers import Real

from api.models.analysis import Analysis
from api.models.repository import Repository


class AnalysisPersistenceService:

    SCORE_FIELDS = (
        "popularity_score",
        "activity_score",
        "documentation_score",
        "maintainability_score",
        "code_quality_score",
        "community_score",
        "overall_score",
    )

    @classmethod
    def _validate_scores(cls, scores):
        """
        Validate all analysis scores before database persistence.
        """

        if not isinstance(scores, dict):
            raise ValueError("Scores must be a dictionary.")

        validated_scores = {}

        for field in cls.SCORE_FIELDS:

            if field not in scores:
                raise ValueError(
                    f"Missing required score: {field}."
                )

            score = scores[field]

            if isinstance(score, bool) or not isinstance(score, Real):
                raise ValueError(
                    f"{field} must be a numeric value."
                )

            if not math.isfinite(score):
                raise ValueError(
                    f"{field} must be a finite number."
                )

            if not 0 <= score <= 100:
                raise ValueError(
                    f"{field} must be between 0 and 100."
                )

            if not float(score).is_integer():
                raise ValueError(
                    f"{field} must be a whole number."
                )

            validated_scores[field] = int(score)

        return validated_scores

    @staticmethod
    def _validate_category(category):

        if not isinstance(category, str):
            raise ValueError("Category must be a string.")

        category = category.strip()

        if not category:
            raise ValueError("Category cannot be empty.")

        return category

    @staticmethod
    def _validate_summary(summary):

        if summary is None:
            return ""

        if not isinstance(summary, str):
            raise ValueError("Summary must be a string.")

        return summary.strip()

    @staticmethod
    def _format_recommendations(recommendations):

        if recommendations is None:
            return ""

        if not isinstance(recommendations, (list, tuple)):
            raise ValueError(
                "Recommendations must be a list or tuple of strings."
            )

        if not all(
            isinstance(item, str)
            for item in recommendations
        ):
            raise ValueError(
                "Every recommendation must be a string."
            )

        return "\n".join(
            item.strip()
            for item in recommendations
        )

    @classmethod
    def save_analysis(
        cls,
        repository,
        category,
        scores,
        summary,
        recommendations,
        user=None,
    ):
        """
        Validate and persist a repository analysis.
        """

        if not isinstance(repository, Repository):
            raise ValueError("A valid repository instance is required.")

        validated_category = cls._validate_category(category)
        validated_scores = cls._validate_scores(scores)
        validated_summary = cls._validate_summary(summary)

        formatted_recommendations = cls._format_recommendations(
            recommendations
        )

        return Analysis.objects.create(
            repository=repository,
            user=user,
            project_type=validated_category,
            popularity_score=validated_scores["popularity_score"],
            activity_score=validated_scores["activity_score"],
            documentation_score=validated_scores["documentation_score"],
            maintainability_score=validated_scores["maintainability_score"],
            code_quality_score=validated_scores["code_quality_score"],
            community_score=validated_scores["community_score"],
            overall_score=validated_scores["overall_score"],
            score_version=Analysis.CURRENT_SCORE_VERSION,
            ai_summary=validated_summary,
            recommendations=formatted_recommendations,
        )
