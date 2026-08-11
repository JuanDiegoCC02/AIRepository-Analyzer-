


class AnalysisResultService:

    @staticmethod
    def get_level (overall_score):

        if overall_score >= 90:
            return "Excellent"

        if overall_score >= 75:
            return "Good"

        if overall_score >= 50:
            return "Average"
        return "Needs Improvement"


    @classmethod
    def build (cls, analysis_scores):

        overall_score = analysis_scores.get(
            "overall_score",
            0
        )

        level = analysis_scores.get(
            "level"
        )

        if not level:
            level + cls.get_level(
                overall_score
            )

        return {
            "overall":{
                "score": overall_score,
                "level": level,
            },

            "dimensions": {
                "popularity": analysis_scores.get(
                    "popularity_score",
                    0
                ),

                "activity": analysis_scores.get(
                    "activity_score",
                     0
                ),

                "documentation": analysis_scores.get(
                    "documentation_score",
                    0
                ),

                "maintainability": analysis_scores.get(
                    "maintainability_score",
                    0
                ),

                "code_quality": analysis_scores.get(
                    "code_quality_score",
                    0
                ),

                "community": analysis_scores.get(
                    "community_score",
                    0
                ),
                
            }
        }
