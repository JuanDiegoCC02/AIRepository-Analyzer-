


class RecommendationService:

    # popularity
    @staticmethod
    def popularity(score):

        if score < 50:
            return (
                "Increase project visibility by improving the "
                "README, project description, documentation and "
                "community engagement."
            )

        if score < 70:
            return (
                "Consider improving project visibility and "
                "community adoption through better documentation "
                "and regular project updates."
            )
        return None



    # activity
    @staticmethod
    def activity(score):

        if score < 50:
            return (
                "Repository activity is low. Consider making "
                "more frequent commits and maintaining a regular "
                "development cycle."
            )

        if score < 70:
            return (
                "Consider increasing development activity through "
                "regular updates, maintenance and feature improvements."
            )
        return None


    
    # documentation
    @staticmethod
    def documentation(score):

        if score < 50:
            return (
                "Improve the project documentation by expanding "
                "the README with installation instructions, usage "
                "examples, project structure and development guidelines."
            )

        if score < 70:
            return (
                "Improve the README and project documentation by "
                "adding more detailed usage instructions and examples."
            )

        if score < 85:
            return (
                "Consider expanding the documentation with additional "
                "examples and development guidelines."
            )
        return None


    
    # maintainability
    @staticmethod
    def maintainability(score):

        if score < 50:
            return (
                "Improve maintainability by reviewing project "
                "structure, reducing code complexity and separating "
                "responsibilities between components and services."
            )

        if score < 70:
            return (
                "Consider improving project structure and reducing "
                "unnecessary complexity to make future maintenance easier."
            )
        return None


    # code quality
    @staticmethod
    def code_quality(score):

        if score < 50:
            return (
                "Code quality requires significant improvement. "
                "Consider introducing automated testing, improving "
                "code organization and applying consistent coding standards."
            )

        if score < 70:
            return (
                "Improve code quality by increasing test coverage, "
                "reducing duplicated code and maintaining consistent "
                "coding practices."
            )

        if score < 85:
            return (
                "Consider increasing automated test coverage and "
                "reviewing areas of the codebase that may contain "
                "unnecessary complexity."
            )
        return None



    # community
    @staticmethod
    def community(score):

        if score < 50:
            return (
                "Community engagement is limited. Consider improving "
                "project documentation, contribution guidelines and "
                "issue management to encourage external contributions."
            )

        if score < 70:
            return (
                "Improve community engagement by maintaining clear "
                "contribution guidelines and responding regularly to "
                "issues and discussions."
            )
        return None


    
    # overall
    @staticmethod
    def overall(score):

        if score < 50:
            return (
                "The repository requires significant improvements "
                "across multiple quality dimensions before it can "
                "be considered production ready."
            )

        if score < 70:
            return (
                "The repository would benefit from improvements "
                "across several quality dimensions before production use."
            )

        if score < 85:
            return (
                "The repository is in good condition but still has "
                "several opportunities for improvement."
            )
        return None



    # evolution
    @staticmethod
    def evolution(evolution):

        if not evolution:
            return None

        if not evolution.get("available"):
            return None

        trend = evolution.get(
            "overall_trend"
        )

        difference = evolution.get(
            "overall_difference",
            0
        )

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
        return None


    
    # score differences
    @staticmethod
    def score_changes(evolution):

        if not evolution:
            return []

        if not evolution.get("available"):
            return []

        changes = evolution.get(
            "score_changes",
            {}
        )

        recommendations = []

        for score_name, difference in changes.items():

            if difference <= -10:

                readable_name = score_name.replace(
                    "_score",
                    ""
                ).replace(
                    "_",
                    " "
                )

                recommendations.append(
                    f"{readable_name.capitalize()} has declined "
                    f"by {abs(difference)} points. Prioritize "
                    f"improvements in this area."
                )

        return recommendations

