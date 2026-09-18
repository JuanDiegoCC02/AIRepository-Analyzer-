from api.services.analysis_history_service import AnalysisHistoryService
from api.services.analysis_comparison_service import AnalysisComparisonService


class AnalysisEvaluationService:

    @classmethod
    def generate(cls, repository, current_analysis):

        history = AnalysisHistoryService.get_history(
            repository
        )

        if history is None:
            return cls._unavailable_response()

        history = list(history)

        if len(history) < 2:
            return cls._unavailable_response()

        previous_analysis = None

        for analysis in history:
            if analysis.id != current_analysis.id:
                previous_analysis = analysis
                break

        if previous_analysis is None:
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
        difference = overall.get("difference", 0)

        return {
            "available": True,
            "current_analysis_id": current_analysis.id,
            "previous_analysis_id": previous_analysis.id,
            "comparison": comparison,
            "overall_trend": trend,
            "overall_difference": difference,
        }

    
        
