


class OverallScoreService:

    @staticmethod
    def calculate(
        popularity,
        activity,
        documentation,
        maintainability,
        code_quality,
        community,
    ):

        total = (
            popularity +
            activity +
            documentation +
            maintainability +
            code_quality+
            community
        )

        return round(total / 6)