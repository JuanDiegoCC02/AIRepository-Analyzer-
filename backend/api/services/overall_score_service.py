


class OverallScoreService:

    @staticmethod
    def calculate(
        popularity,
        activity,
        documentation,
        maintainability,
        code_quality,
    ):

        total = (
            popularity +
            activity +
            documentation +
            maintainability +
            code_quality
        )

        return round(total / 5)