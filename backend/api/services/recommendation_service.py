


class RecommendationService:

    @staticmethod
    def generate(scores):

        recommendations = []
        popularity = scores["popularity_score"]
        activity = scores["activity_score"]
        documentation = scores["documentation_score"]
        maintainability = scores["maintainability_score"]
        overall = scores["overall_score"]

       
        # Popularity
        if popularity >= 90:

            recommendations.append(
                "Repository has excellent popularity."
            )

        elif popularity >= 70:

            recommendations.append(
                "Repository has good community adoption."
            )

        else:

            recommendations.append(
                "Repository could benefit from increased community visibility."
            )

       
        # Activity
        if activity >= 90:

            recommendations.append(
                "Repository is actively maintained."
            )

        elif activity >= 70:

            recommendations.append(
                "Repository shows regular development activity."
            )

        else:

            recommendations.append(
                "Repository activity appears limited."
            )

        
        # Documentation
        if documentation >= 90:

            recommendations.append(
                "Documentation quality is excellent."
            )

        elif documentation >= 70:

            recommendations.append(
                "Documentation is good but could be expanded."
            )

        else:

            recommendations.append(
                "Improve documentation by expanding the README and project guides."
            )


        # Maintainability
        if maintainability >= 90:

            recommendations.append(
                "Repository follows strong maintainability practices."
            )

        elif maintainability >= 70:

            recommendations.append(
                "Maintainability is acceptable with room for improvement."
            )

        else:

            recommendations.append(
                "Improve repository structure and reduce technical debt."
            )

       
        # Overall
        if overall >= 90:

            recommendations.append(
                "Overall repository quality is outstanding."
            )

        elif overall >= 75:

            recommendations.append(
                "Repository demonstrates solid engineering practices."
            )

        else:

            recommendations.append(
                "Repository would benefit from improvements across multiple areas."
            )

        return recommendations