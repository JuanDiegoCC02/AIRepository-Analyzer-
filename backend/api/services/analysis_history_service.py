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
    def get_previous(repository):
        """
        Return the analysis immediately preceding
        the latest analysis.

        Returns None when fewer than two analyses exist.
        """

        analyses = (
            Analysis.objects
            .filter(repository=repository)
            .order_by("-created_at", "-id")[1:2]
        )

        return analyses[0] if analyses else None



    @staticmethod
    def get_best(repository):
        """
        Return the analysis with the highest overall score.

        When multiple analyses have the same score,
        the most recent one is returned.
        """

        return (
            Analysis.objects
            .filter(repository=repository)
            .order_by("-overall_score", "-created_at", "-id")
            .first()
        )



    @staticmethod
    def get_worst(repository):
        """
        Return the analysis with the lowest overall score.

        When multiple analyses have the same score,
        the most recent one is returned.
        """

        return (
            Analysis.objects
            .filter(repository=repository)
            .order_by("overall_score", "-created_at", "-id")
            .first()
        )

