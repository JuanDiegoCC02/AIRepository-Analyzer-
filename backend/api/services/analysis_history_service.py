from api.models.analysis import Analysis


class AnalysisHistoryService:

    @staticmethod
    def get_history(repository):
        """
        Return all analyses for a repository,
        ordered from newest to oldest.
        """

        return (
            Analysis.objects
            .filter(repository=repository)
            .order_by("-created_at", "-id")
        )



    @staticmethod
    def get_latest(repository):
        """
        Return the most recent analysis for a repository.
        """

        return (
            Analysis.objects
            .filter(repository=repository)
            .order_by("-created_at", "-id")
            .first()
        )



    @staticmethod
    def get_best(repository):
        return Analysis.objects.filter(
            repository=repository
        ).order_by(
            "-overall_score"
        ).first()

    @staticmethod
    def get_worst(repository):
        return Analysis.objects.filter(
            repository=repository
        ).order_by(
            "overall_score"
        ).first()


    # comparison structure
    @staticmethod
    def compare_latest(repository):
        latest = AnalysisHistoryService.get_latest(
            repository
        )

        previous = AnalysisHistoryService.get_previous(
            repository
        )

        if not latest:
            return {
                "available": False,
                "reason": "No analysis history available."
            }

        if not previous:
            return {
                "available": False,
                "reason": "Not enough analysis history."
            }

        difference = (
            latest.overall_score
            - previous.overall_score
        )

        if difference > 0:
            trend = "Improving"

        elif difference < 0:
            trend = "Declining"

        else:
            trend = "Stable"


        return {
            "available": True,

            "current_score": (latest.overall_score),

            "previous_score": (previous.overall_score),

            "difference": difference,

            "trend": trend,

            "analyzed_at": (latest.created_at),
        }