from api.models.analysis import Analysis


class AnalysisPersistenceService:

    @staticmethod
    def save_analysis (
        repository,
        category,
        scores,
        summary,
        recommendations,
    ):

       # save analysis
            analysis = Analysis.objects.create(
                  
                repository=repository,

                project_type=category, 
                
                    popularity_score = scores["popularity_score"],
    
                    activity_score = scores["activity_score"],
    
                    documentation_score = scores["documentation_score"],
    
                    maintainability_score = scores["maintainability_score"],

                    code_quality_score = scores["code_quality_score"],
    
                    community_score = scores["community_score"],
                    
                    overall_score = scores["overall_score"],
    
                    ai_summary = summary,
    
                    recommendations = "\n".join(recommendations),
                    
            )

            return analysis 
        
        