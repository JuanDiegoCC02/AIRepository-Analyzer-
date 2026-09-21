


class RecommendationService:

    LOW_SCORE = 50
    MODERATE_SCORE = 70
    GOOD_SCORE = 85

    SIGNIFICANT_DECLINE = 10
    MAX_RECOMMENDATIONS = 7

    SCORE_METHODS = [
        ("popularity", "popularity_score"),
        ("activity", "activity_score"),
        ("documentation", "documentation_score"),
        ("maintainability", "maintainability_score"),
        ("code_quality", "code_quality_score"),
        ("community", "community_score"),
        ("overall", "overall_score"),
    ]


    @staticmethod
    def _normalize_score(score):

        if not isinstance(score, (int, float)):
            return 0

        return max(0, min(score, 100))



    @staticmethod
    def popularity(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Increase project visibility by improving the "
                "README, project description, documentation and "
                "community engagement."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Consider improving project visibility and "
                "community adoption through better documentation "
                "and regular project updates."
            )

        return None



    @staticmethod
    def activity(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Repository activity is low. Consider making "
                "more frequent commits and maintaining a regular "
                "development cycle."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Consider increasing development activity through "
                "regular updates, maintenance and feature improvements."
            )

        return None


    
    @staticmethod
    def documentation(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Improve the project documentation by expanding "
                "the README with installation instructions, usage "
                "examples, project structure and development guidelines."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Improve the README and project documentation by "
                "adding more detailed usage instructions and examples."
            )

        if score < RecommendationService.GOOD_SCORE:
            return (
                "Consider expanding the documentation with additional "
                "examples and development guidelines."
            )

        return None


    
    @staticmethod
    def maintainability(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Improve maintainability by reviewing project "
                "structure, reducing code complexity and separating "
                "responsibilities between components and services."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Consider improving project structure and reducing "
                "unnecessary complexity to make future maintenance easier."
            )

        return None



    @staticmethod
    def code_quality(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Code quality requires significant improvement. "
                "Consider introducing automated testing, improving "
                "code organization and applying consistent coding standards."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Improve code quality by increasing test coverage, "
                "reducing duplicated code and maintaining consistent "
                "coding practices."
            )

        if score < RecommendationService.GOOD_SCORE:
            return (
                "Consider increasing automated test coverage and "
                "reviewing areas of the codebase that may contain "
                "unnecessary complexity."
            )

        return None



    @staticmethod
    def community(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "Community engagement is limited. Consider improving "
                "project documentation, contribution guidelines and "
                "issue management to encourage external contributions."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "Improve community engagement by maintaining clear "
                "contribution guidelines and responding regularly to "
                "issues and discussions."
            )

        return None


    
    @staticmethod
    def overall(score):

        if score < RecommendationService.LOW_SCORE:
            return (
                "The repository requires significant improvements "
                "across multiple quality dimensions before it "
                "can be considered production ready."
            )

        if score < RecommendationService.MODERATE_SCORE:
            return (
                "The repository would benefit from improvements "
                "across several quality dimensions before production use."
            )

        if score < RecommendationService.GOOD_SCORE:
            return (
                "The repository is in good condition but still has "
                "several opportunities for improvement."
            )

        return None



    @staticmethod
    def evaluation(evaluation):

        if not isinstance(evaluation, dict):
            return None

        if not evaluation.get("available"):
            return None

        trend = evaluation.get("overall_trend")
        difference = evaluation.get("overall_difference")

        if not isinstance(difference, (int, float)):
            return None

        if trend == "Declining":
            return (
                f"The repository's overall score has decreased "
                f"by {abs(difference)} points. Review recent changes "
                f"and prioritize the analysis areas showing the "
                f"largest declines."
            )

        if trend == "Stable":
            return (
                "Repository quality has remained relatively stable. "
                "Continue regular maintenance and monitor future analyses."
            )

        if trend == "Improving":
            return None

        return None


    
    # score differences
    @staticmethod
    def score_changes(evaluation):

        if not isinstance(evaluation, dict):
            return []

        if not evaluation.get("available"):
            return []

        comparison = evaluation.get("comparison")

        if not isinstance(comparison, dict):
            return []

        recommendations = []

        for score_name, data in comparison.items():

            if score_name == "overall":
                continue

            if not isinstance(data, dict):
                continue

            difference = data.get("difference")
            trend = data.get("trend")

            if not isinstance(difference, (int, float)):
                continue

            if trend != "Declining":
                continue

            if difference >= -RecommendationService.SIGNIFICANT_DECLINE:
                continue

            readable_name = (
                score_name
                .replace("_score", "")
                .replace("_", " ")
            )

            recommendations.append(
                f"{readable_name.capitalize()} has declined "
                f"by {abs(difference)} points. Prioritize "
                f"improvements in this area."
            )

        return recommendations


   
    @classmethod
    def generate(cls, analysis_scores, evaluation=None):

        if not isinstance(analysis_scores, dict):
            analysis_scores = {}

        recommendations = []

        for method_name, score_name in cls.SCORE_METHODS:

            score = cls._normalize_score(
                analysis_scores.get(score_name)
            )

            method = getattr(cls, method_name)

            recommendation = method(score)

            if recommendation:
                recommendations.append(recommendation)

        evaluation_recommendation = cls.evaluation(
            evaluation
        )

        if evaluation_recommendation:
            recommendations.append(
                evaluation_recommendation
            )

        recommendations.extend(
            cls.score_changes(evaluation)
        )

        if not recommendations:
            recommendations.append(
                "No major improvements are currently required. "
                "Continue monitoring repository quality and "
                "maintaining regular development activity."
            )

        return recommendations[:cls.MAX_RECOMMENDATIONS]