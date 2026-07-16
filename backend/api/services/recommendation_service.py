


class RecommendationService:

    @staticmethod
    def generate(analysis):

        recommendations = []

        if analysis["documentation_score"] < 70:
            recommendations.append(
                "Improve the project documentation by expanding the README."
            )

        if analysis["activity_score"] < 60:
            recommendations.append(
                "Repository activity is low. Consider making more frequent commits."
            )

        if analysis["maintainability_score"] < 70:
            recommendations.append(
                "Improve maintainability by reducing technical debt and reviewing open issues."
            )

        if analysis["popularity_score"] < 60:
            recommendations.append(
                "Increase project visibility through documentation and community engagement."
            )

        if not recommendations:
            recommendations.append(
                "This repository follows good development practices."
            )

        return recommendations
