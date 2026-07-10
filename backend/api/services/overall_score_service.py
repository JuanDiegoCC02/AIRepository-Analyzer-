


class OverallScoreService:
    @staticmethod
    def calculate(
        popularity_score,
        activity_score,
        documentation_score,
        maintainability_score,
    ):
        
        overall_score = (
            popularity_score
            + activity_score
            + documentation_score
            +maintainability_score
        ) / 4

        return round (overall_score)