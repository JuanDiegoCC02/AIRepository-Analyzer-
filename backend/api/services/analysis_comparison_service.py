
import math
from numbers import Real


class AnalysisComparisonService:
    """
    Compares repository analysis scores and determines their trends.
    """

    SCORE_FIELDS = {
        "popularity": "popularity_score",
        "activity": "activity_score",
        "documentation": "documentation_score",
        "maintainability": "maintainability_score",
        "code_quality": "code_quality_score",
        "community": "community_score",
        "overall": "overall_score",
    }

    STABLE_THRESHOLD = 1

    @staticmethod
    def _validate_score(score, field_name="Score"):
        """
        Validate that a score is numeric, finite, and between 0 and 100.
        """
        if isinstance(score, bool) or not isinstance(score, Real):
            raise ValueError(f"{field_name} must be a numeric value.")

        if not math.isfinite(score):
            raise ValueError(f"{field_name} must be finite.")

        if not 0 <= score <= 100:
            raise ValueError(f"{field_name} must be between 0 and 100.")

        return score

    @classmethod
    def calculate_difference(cls, current_score, previous_score):
        """
        Calculate the difference between two valid scores.

        Returns None when either score is unavailable.
        """
        if current_score is None or previous_score is None:
            return None

        current_score = cls._validate_score(
            current_score,
            "Current score",
        )
        previous_score = cls._validate_score(
            previous_score,
            "Previous score",
        )

        return round(current_score - previous_score, 2)

    @classmethod
    def determine_trend(cls, difference):
        """
        Classify a score difference as improving, declining, or stable.
        """
        if difference is None:
            return "Unavailable"

        if isinstance(difference, bool) or not isinstance(difference, Real):
            raise ValueError("Difference must be a numeric value.")

        if not math.isfinite(difference):
            raise ValueError("Difference must be finite.")

        if difference > cls.STABLE_THRESHOLD:
            return "Improving"

        if difference < -cls.STABLE_THRESHOLD:
            return "Declining"

        return "Stable"

    @classmethod
    def compare_score(cls, current_score, previous_score):
        """
        Compare one score and return its values, difference, and trend.
        """
        difference = cls.calculate_difference(
            current_score,
            previous_score,
        )

        return {
            "current": current_score,
            "previous": previous_score,
            "difference": difference,
            "trend": cls.determine_trend(difference),
        }

    @classmethod
    def compare(cls, current_analysis, previous_analysis):
        """
        Compare two analyses belonging to the same repository.

        Returns an empty dictionary if either analysis is missing or
        if both analyses identify different repositories.
        """
        if current_analysis is None or previous_analysis is None:
            return {}

        current_repository_id = getattr(
            current_analysis,
            "repository_id",
            None,
        )
        previous_repository_id = getattr(
            previous_analysis,
            "repository_id",
            None,
        )

        # When repository IDs are available, they must match.
        if (
            current_repository_id is not None
            or previous_repository_id is not None
        ) and current_repository_id != previous_repository_id:
            return {}

        comparison = {}

        for name, field in cls.SCORE_FIELDS.items():
            current_score = getattr(
                current_analysis,
                field,
                None,
            )
            previous_score = getattr(
                previous_analysis,
                field,
                None,
            )

            comparison[name] = cls.compare_score(
                current_score,
                previous_score,
            )

        return comparison
