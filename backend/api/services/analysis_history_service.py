
from api.models.analysis import Analysis


# Distinguishes an omitted user argument from an explicit user=None.
_USER_NOT_PROVIDED = object()


class AnalysisHistoryService:

    @staticmethod
    def _get_queryset(repository, user=_USER_NOT_PROVIDED):
        queryset = Analysis.objects.filter(repository=repository)

        if user is not _USER_NOT_PROVIDED:
            if user is None:
                queryset = queryset.filter(user__isnull=True)
            else:
                queryset = queryset.filter(user=user)

        return queryset

    @classmethod
    def get_history(cls, repository, user=_USER_NOT_PROVIDED):
        return (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")
        )

    @classmethod
    def get_latest(cls, repository, user=_USER_NOT_PROVIDED):
        return (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")
            .first()
        )

    @classmethod
    def get_previous(cls, repository, user=_USER_NOT_PROVIDED):
        analyses = (
            cls._get_queryset(repository, user)
            .order_by("-created_at", "-id")[1:2]
        )

        return analyses[0] if analyses else None

    @classmethod
    def get_best(cls, repository, user=_USER_NOT_PROVIDED):
        return (
            cls._get_queryset(repository, user)
            .order_by("-overall_score", "-created_at", "-id")
            .first()
        )

    @classmethod
    def get_worst(cls, repository, user=_USER_NOT_PROVIDED):
        return (
            cls._get_queryset(repository, user)
            .order_by("overall_score", "-created_at", "-id")
            .first()
        )
