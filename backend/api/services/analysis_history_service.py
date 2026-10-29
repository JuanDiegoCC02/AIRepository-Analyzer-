
from api.models.analysis import Analysis


class AnalysisHistoryService:

    @staticmethod
    def _get_queryset(repository, user=None):
        queryset = Analysis.objects.filter(repository=repository)

        if user is not None:
            queryset = queryset.filter(user=user)

        return queryset

    @classmethod
    def get_history(cls, repository, user=None):
        return (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")
        )

    @classmethod
    def get_latest(cls, repository, user=None):
        return (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")
            .first()
        )

    @classmethod
    def get_previous(cls, repository, user=None):
        analyses = (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")[1:2]
        )

        return analyses[0] if analyses else None

    @classmethod
    def get_best(cls, repository, user=None):
        return (
            cls._get_queryset(repository, user)
            .order_by("-overall_score", "-created_at", "-id")
            .first()
        )

    @classmethod
    def get_worst(cls, repository, user=None):
        return (
            cls._get_queryset(repository, user)
            .order_by("overall_score", "-created_at", "-id")
            .first()
        )
