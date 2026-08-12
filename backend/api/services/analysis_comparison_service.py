


class AnalysisComparisonService:

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


    @classmethod
    def calculate_difference(cls, current_score, previous_score):

        difference = (current_score - previous_score)

        return round(difference, 2,)


    @classmethod
    def determine_trend(cls, difference):

        if difference > cls.STABLE_THRESHOLD:
            return "Improving"

        if difference < -cls.STABLE_THRESHOLD:
            return "Declining"

        return "Stable"


    @classmethod
    def compare_score(cls, current_score, previous_score):

        difference = cls.calculate_difference(
            current_score,
            previous_score,
        )

        trend = cls.determine_trend(
            difference
        )

        return {
            "current": current_score,
            "previous": previous_score,
            "difference": difference,
            "trend": trend,
        }


    @classmethod
    def compare(cls, current_analysis, previous_analysis):

        comparison = {}

        for name, field in cls.SCORE_FIELDS.items():

            current_score = getattr(
                current_analysis,
                field,
            )

            previous_score = getattr(
                previous_analysis,
                field,
            )

            comparison[name] = cls.compare_score(
                current_score,
                previous_score,
            )

        return comparison