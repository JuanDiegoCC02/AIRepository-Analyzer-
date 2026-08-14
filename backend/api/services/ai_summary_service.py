



class AISummaryService:

    # score level
    @staticmethod
    def score_level(score):
        if score >= 90:
            return "excellent"
        
        if score >= 80:

            return "very goood"
        if score >= 70:
            return "good"
        
        if score >= 50:
            return "average"
        
        return "needs improvement"


    # tecnology
    @staticmethod
    def technology_summary(technolohies):
        if not technolohies:
            return (
                "The repository's primary technolohy could not be determined."
            )

        main = technolohies [0]

        language = main.get(
            "language",
            "Unknown"
        )

        percentage = main.get(
            "percentage",
            0
        )

        return (
            f"The repository is primarily written in {language}, wich represents approximately {percentage}& of the detected code." 
        )


    # popularity
    @staticmethod
    def popularity_summary(score, stars):

        level = AISummaryService.score_level(score)

        if stars is None:
            return (
                f"The repository demonstrates {level} community popularity."
            )

        return (
            f"The repository demostrates {level} community popularity with {stars:,} GitHub stars."
        )


    # activity
    @staticmethod
    def activity_summary(score):

        level = AISummaryService.score_level(
            score
        )

        if score >= 80:
            return (
                "Development activity is high, indicating that the project receives regular development attention."
            )

        if score >= 60:
            return ( 
                "Development activity is relatively consistent, although there is room for increased development activity."
            )

        return(
            "Development activity  is relatively low and may indicate reduced maintenance activity."
        )


    # documentation
    @staticmethod 
    def documentation_summary(score):
        if score >= 90:
            return(
                 "Documentation quality is excellent and provides strong support for understanding the project."
            )

        if score >= 70:
            return (
                "Documentation quality is good although some areas could still be expanded."
            )

        if score >= 50:
            return (
                "Documentation is acceptable but could be improved to make the project easier to understand."
            )

        return (
            "Documentation quality is limited and should be significantly improved."
        )


    @staticmethod
    def maintainability_summary(score):
        if score >= 90:
            return  (
                "The repository demonstrates excellent maintainability characteristics."
            )

        if score >= 70: 
            return (
                "The repository appears realtively easy to maintain."
            )

        if score >= 50:
            return (
                "Maintainability is acceptable but there are areas that could be imrproved."
            )

        return (
            "The repository may present maintainability challenges and would benefit from structural improvements."
        ) 


    # code quality
    @staticmethod
    def code_quality_summary(score):
        if score >= 90:
            return (
                "Code quality indicators are excellent."
            )

        if score >= 70:
            return (
                "The repository demonstrates good code quality characteristics."
            )

        if score >= 50:
            return (
                "Code quality is moderate and could benedit from additional improvements."
            )

        return (
            "Code quality requires significant improvements."
        )


    # community
    @staticmethod
    def community_summary(score):
        if score >= 90:
            return (
                "Community participation is outstanding, "
                "indicating strong engagement around "
                "the project."
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
            "Community engagement is currently limited."
        )

  
    # evolution
    @staticmethod
    def evolution_summary(evolution):
        if not evolution:
            return (
                "Historical repository evolution "
                "is not available."
            )
        
        if not evolution.get("available"):
            return (
                "There is not enough historical data "
                "to determine the repository's evolution."
            )
        trend = evolution.get(
            "overall_trend"
        )
        difference = evolution.get(
            "overall_difference",
            0
        )

        if trend == "Improving":
            return (
                f"The repository is showing an improving "
                f"overall trend, with the score increasing "
                f"by {difference} points compared with "
                f"the previous analysis."
            )

        if trend == "Declining":
            return (
                f"The repository is showing a declining "
                f"overall trend, with the score decreasing "
                f"by {abs(difference)} points compared "
                f"with the previous analysis."
            )

        return (
            "The repository's overall quality remains "
            "relatively stable compared with the "
            "previous analysis."
        )


    # main summary generator
    @ classmethod
    def generate ( 
        cls, 
        github_repository,
        category,
        technologies,
        analysis_scores,
        evolution=None
        ): 

        repository_name = github_repository.get(
            "name",
            "Unknown Repository"
        )

        description = github_repository.get(
            "description"
        )

        language = github_repository.get(
            "language",
            "Unknown"
        )

        stars = github_repository.get(
            "stargazers_count",
            0
        )

        overall_score = analysis_scores.get(
            "activity_score",
            0
        )

        activity_score = analysis_scores.get(
            "activity_score",
            0
        )

        documentation_score = analysis_scores.get(
            "documentation_score",
            0
        )

        maintainability_score = analysis_scores.get(
            "maintainability",
            0
        )

        code_quality_score = analysis_scores.get(
            "code_quality_score",
            0
        )

        community_score = analysis_scores.get(
            "community_score",
            0
        )

        popularity_score = analysis_scores.get(
            "popularity_score",
            0
        )


        #introduction
        if description:
            introduction = (
                f"{repository_name} is classified as a {category} project primarily written in {language}."
                f"The repository describes itself as: {description}"
            )
        else:
            introduccion = (
                f"{repository_name} is classified as a {category} project primarily written in {language}."
            )


        score_summary = (f"The repository currently has an overall score of {overall_score}/100.")

        technology_summary = cls.technology_summary(technologies)

        popularity_summary = cls.popularity_summary(popularity_score, stars)

        activity_summary = cls.activity_summary(activity_score)

        documentation_summary = cls.documentation_summary(documentation_score)

        maintainability_summary = cls.maintainability_summary(maintainability_score)

        code_quality_summary = cls.code_quality_summary(code_quality_score)

        community_summary = cls.community_summary(community_score)

        evolution_summary = cls.evolution_summary(evolution)

        summary = " ".join(
        [
            introduction,
            score_summary,
            technology_summary,
            popularity_summary,
            activity_summary,
            documentation_summary,
            maintainability_summary,
            code_quality_summary,
            community_summary,
            evolution_summary,
        ]
    )

        return summary