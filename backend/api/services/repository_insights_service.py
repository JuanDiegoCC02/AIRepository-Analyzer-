


class RepositoryInsightsService:

    @staticmethod
    def popularity(score):

        if score >= 90:
            return (
                "This repository is highly popular within "
                "the GitHub community."
            )

        if score >= 70:
            return (
                "This repository has solid community adoption."
            )

        if score >= 50:
            return (
                "This repository has moderate popularity."
            )

        return (
            "This repository has limited community adoption."
        )


    @staticmethod
    def activity(score):

        if score >= 80:
            return (
                "Development activity is high."
            )

        if score >= 60:
            return (
                "The repository receives regular updates."
            )

        return (
            "Repository activity is relatively low."
        )


    @staticmethod
    def documentation(score):

        if score >= 90:
            return (
                "Documentation is excellent and comprehensive."
            )

        if score >= 70:
            return (
                "Documentation quality is good."
            )

        if score >= 50:
            return (
                "Documentation is acceptable but could be improved."
            )

        return (
            "Documentation quality is poor."
        )


    @staticmethod
    def maintainability(score):

        if score >= 90:
            return (
                "Code maintainability is excellent."
            )

        if score >= 70:
            return (
                "The repository is easy to maintain."
            )

        if score >= 50:
            return (
                "Maintainability is acceptable."
            )

        return (
            "The repository may be difficult to maintain."
        )


    @staticmethod
    def code_quality(score):

        if score >= 90:
            return (
                "Code quality indicators are excellent."
            )

        if score >= 70:
            return (
                "Code quality indicators are strong."
            )

        if score >= 50:
            return (
                "Code quality indicators are moderate."
            )

        return (
            "Code quality indicators are limited."
        )
    

    @staticmethod
    def community(score):

        if score >= 90:
            return (
                "Community participation is outstanding."
            )

        if score >= 70:
            return (
                "Community engagement is strong."
            )

        if score >= 50:
            return (
                "Community activity is moderate."
            )

        return (
            "Community engagement is limited."
        )


    @staticmethod
    def overall(score):

        if score >= 90:
            return (
                "Overall repository health is excellent."
            )

        if score >= 80:
            return (
                "Overall repository health is very good."
            )

        if score >= 70:
            return (
                "Repository quality is good."
            )

        if score >= 50:
            return (
                "Repository quality is average."
            )

        return (
            "Repository requires significant improvements."
        )


    @staticmethod
    def technology(technologies):

        if not technologies:
            return None

        main = technologies[0]

        return (
            f"The dominant technology is "
            f"{main['language']} "
            f"({main['percentage']}%)."
        )


    @staticmethod
    def project_type(project_type):

        if not project_type:
            return None

        return (
            f"The repository is classified as "
            f"{project_type}."
        )


    @staticmethod
    def production_ready(score):

        if score >= 85:
            return (
                "Based on the analyzed metrics, the repository "
                "appears suitable for production environments."
            )

        if score >= 70:
            return (
                "The repository appears suitable for development "
                "and testing environments, but additional validation "
                "may be required before production deployment."
            )

        return (
            "The repository requires additional improvements "
            "before it should be considered for production deployment."
        )


    @staticmethod
    def evaluation(evaluation_data):
        if not evaluation_data:
            return None

        if not evaluation_data.get("available"):
            return (
                "Historical evaluation is not available "
                "because there is not enough analysis data."
            )
        
        trend = evaluation_data.get(
            "overall_trend"
        )

        difference = evaluation_data.get(
            "overall_difference",
            0
        )

        if trend == "Improving":
            return (
                f"Overall repository quality is improving "
                f"with an increase of {difference} points "
                f"compared with the previous analysis."
            )
        return(
            "Overall repository quality remains stable "
            "compared with the previous analysis."
        )


    @staticmethod
    def evaluation_details(evaluation_data):
        if not evaluation_data:
            return []

        if not evaluation_data.get("available"):
            return []

        comparison = evaluation_data.get(
            "comparison"
        )

        if not comparison:
            return[]

        insights = []

        metrics = {
            "activity": "Activity",
            "documentation": "Documentation",
            "maintainability": "Maintainability",
            "code_quality": "Code quality",
            "community": "Community",
            "popularity": "Popularity",
        }

        for metric, label in metrics.items():
            data = comparison.get(metric)

            if not data:
                continue

            trend = data.get("trend")

            difference = data.get(
              "difference",
               0
            )

            if trend == "Improving":
                insights.append(
                  f"{label} improved by "
                  f"{difference} points compared "
                  f"with the previous analysis."
                )

            elif trend == "Declining":
                insights.append(
                  f"{label} declined by "
                  f"{abs(difference)} points compared "
                  f"with the previous analysis."
                )

            elif trend == "Stable":
                insights.append(
                  f"{label} remained stable compared "
                  f"with the previous analysis."
                )

        return insights



        



    @classmethod
    def generate(
        cls,
        repository,
        analysis,
        technologies,
        evaluation=None,
    ):

        insights = []

        # popularity
        insights.append(
            cls.popularity(
                analysis.popularity_score
            )
        )

      
        # activity
        insights.append(
            cls.activity(
                analysis.activity_score
            )
        )

     
        # documentation
        insights.append(
            cls.documentation(
                analysis.documentation_score
            )
        )

     
        # maintainability
        insights.append(
            cls.maintainability(
                analysis.maintainability_score
            )
        )


        # code quality
        insights.append(
            cls.code_quality(
                analysis.code_quality_score
            )
        )

        # community
        insights.append(
            cls.community(
                analysis.community_score
            )
        )

      
        # overall
        insights.append(
            cls.overall(
                analysis.overall_score
            )
        )


        # project type
        project_type = cls.project_type(
            analysis.project_type
        )

        if project_type:
            insights.append(
                project_type
            )

      
        # production readiness
        insights.append(
            cls.production_ready(
                analysis.overall_score
            )
        )

    
        # technology
        technology = cls.technology(
            technologies
        )

        if technology:
            insights.append(
                technology
            )

        # evaluation summary
        evaluation_insight = cls.evaluation(
            evaluation
        )

        if evaluation_insight:
            insights.append(
                evaluation_insight
            )


        # detailed evaluation
        evaluation_details = cls.evaluation_details(
            evaluation
        )

        insights.extend(
            evaluation_details
        )

        return insights