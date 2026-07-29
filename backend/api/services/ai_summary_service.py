



class AISummaryService:
    @staticmethod
    def generate(
        repository,
        category,
        technologies,
        scores,
        ):

        main_language = "Unknown"

        if technologies:
            main_language = technologies[0]["language"]

        overall = scores["overall_score"]
        popularity = scores["popularity_score"]
        activity = scores["activity_score"]
        documentation = scores["documentation_score"]
        maintainability = scores["maintainability_score"]
        community = scores["community_score"]

#popularity short phrases 
        if popularity >= 90:
            popularity_text = (
                "The project has exceptional community adoption."
            )
        elif popularity >= 70: 
            popularity_text =(
                "The repository has solid popularity on GitHub."
            )
        else:
            popularity_text = ( 
                "The repository is still growing winthin the community."
            )

#activity short phrases
        if activity >= 80:
            activity_text = (
                "Development activity remains very active."
            )
        elif activity >= 60:
            activity_text = (
                "Documentation is adequate."
            )
        else:
            documentation_text = (
                "Documentation could be significantly improved."
            )

#maintainability short phrases
        if maintainability >= 80:
            maintainability_text = (
                "The codebase appears be well organized and maintainable."
            )
        else:
            maintainability_text = (
                "Maintainability could be improved."
            )

#popularity short phrases
        if community >= 80:
            community_text = (
                "THe repository benefits from a healthy open-source community."
            )
        else:
            community_text = (
                "Community engagement is moderate."
            )

        return (
            f"{repository['name']} is a "
            f"{category} project primarily written in "
            f"{main_language}"
            f"{popularity_text}"
            f"{activity_text}"
            f"{documentation_text}"
            f"{maintainability_text}"
            f"{community_text}"
            f"The overall repository quality score is "
            f"{overall}/100."      
        )
            
