from api.services.analysis_history_service import AnalysisHistoryService
from api.services.analysis_comparison_service import AnalysisComparisonService


class AnalysisEvaluationService:

    VALID_TRENDS = {
        "Improving",
        "Declining",
        "Stable",
    }


    @classmethod
    def generate(cls, repository, current_analysis):

        if repository is None or current_analysis is None:
            return cls._unavailable_response()

        if current_analysis.repository_id != repository.id:
            return cls._unavailable_response(
                "The analysis does not belong to the specified repository."
            )

        previous_analysis = (
            AnalysisHistoryService.get_previous(repository)
        )

        if previous_analysis is None:
            return cls._unavailable_response()

        if previous_analysis.id == current_analysis.id:
            return cls._unavailable_response()

        comparison = AnalysisComparisonService.compare(
            current_analysis,
            previous_analysis,
        )

        if not isinstance(comparison, dict):
            return cls._unavailable_response()

        overall = comparison.get("overall")

        if not isinstance(overall, dict):
            return cls._unavailable_response()

        trend = overall.get("trend")
        difference = overall.get("difference")

        if trend not in cls.VALID_TRENDS:
            return cls._unavailable_response()

        if difference is None:
            return cls._unavailable_response()

        return {
            "available": True,
            "current_analysis_id": current_analysis.id,
            "previous_analysis_id": previous_analysis.id,
            "comparison": comparison,
            "overall_trend": trend,
            "overall_difference": difference,
        }



    @staticmethod
    def _unavailable_response():
        return {
            "available": False,
            "message": "Not enough historical data for comparison.",
            "comparison": None,
        }
        
