from api.services.analysis_history_service import AnalysisHistoryService
from api.services.analysis_comparison_service import AnalysisComparisonService

class AnalysisEvaluationService:

    @classmethod
    def generate(cls, repository, current_analysis):

        history = AnalysisHistoryService.get_history(
            repository
        )

        if history.count() < 2:
            return{
                "available": False,
                "message": "Not enough historical data for comparison.",
                "comparison": None,
            }

        previous_analysis = history[1]

        comparison = AnalysisComparisonService.compare(
            current_analysis,
            previous_analysis,
        )

        overall = comparison.get(
            "overall"
        )

        return{
            "available": True,
            "current_analysis_id": current_analysis.id,
            "previous_analysis_id": previous_analysis.id,
            "comparison": comparison,
            "overall_trend": overall["trend"],
            "overall_difference": overall["difference"],
        }
        
