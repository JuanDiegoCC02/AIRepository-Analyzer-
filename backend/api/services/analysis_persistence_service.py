import math 

from numbers import Real 
from api.models.analysis import Analysis


class AnalysisPersistenceService:

    SCORE_FIELDS = (
        "popularity_score", 
        "activity_score", 
        "documentation_score", 
        "maintainability_score", 
        "code_quality_score", 
        "community_score", 
        "overall_score",
    )

    @classmethod
    def _validate_scores(cls, scores):
        if not isinstance(scores, dict):
            raise ValueError("Scores must be a dictionary.")

        validated_scores = {}

        for field in cls.SCORE_FIELDS:
            if field not in scores:
                raise ValueError(f"Missing required score: {field}.")

            score = scores[field]

            if isinstance(score, bool) or not isinstance(score, Real):
                raise ValueError(f"{field} must be a numeric value.")

            if not math.isfinite(score) or not 0 <= score <= 100:
                raise ValueError(f"{field} must be between 0 and 100.")

            if not float(score).is_integer():
                raise ValueError(f"{field} must be a whole number.")

            validated_scores[field] = int(score)

        return validated_scores



    # saved analysis 
    @staticmethod
    def save_analysis(
        repository,
        category,
        scores,
        summary,
        recommendations,
    ):

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
        
        