from api.models.analysis import Analysis


class AnalysisHistoryService:

    @staticmethod
    def get_history(repository):
        analyses = Analysis.objects.filter(
            repository=repository
        ).order_by(
            "-created_at"
        )
        return analyses


    @staticmethod
    def get_latest(repository):
        return Analysis.objects.filter(
            repository=repository
        ).order_by(
            "-created_at"
        ).first()
    

    @staticmethod
    def get_previous(repository):
        analyses = Analysis.objects.filter(
            repository=repository
        ).order_by(
            "-created_at"
        )

        if analyses.count() < 2:
            return None
        return analyses[1]


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