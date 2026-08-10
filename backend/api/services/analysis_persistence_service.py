from api.models.analysis import Analysis


class AnalysisPersistenceService:

    @staticmethod
    def save (
        repository,
        category,
        analysis_scores,
        summary,
        recommendations,
    ):

       # save analysis
            analysis, created = Analysis.objects.update_or_create(
                repository=repository,
                defaults={
                    "project_type": category,
    
                    "popularity_score": analysis_scores["popularity_score"],
    
                    "activity_score": analysis_scores["activity_score"],
    
                    "documentation_score": analysis_scores["documentation_score"],
    
                    "maintainability_score": analysis_scores["maintainability_score"],
    
                    "community_score": analysis_scores["community_score"],
                    
                    "overall_score": analysis_scores["overall_score"],
    
                    "ai_summary": summary,
    
                    "recommendations": "\n".join(recommendations),
                    
                }
            )

            return analysis, created 
        
        