


class RepositoryInsightsService:


#popularity method
    @staticmethod 
    def popularity(score):
        if score >= 90:
            return "This repository is highly popular winthin the GitHub community."
        
        if score >= 70:
            return "This repository has solid community adoption."
        
        if score >= 50:
            return " This repository has moderate popularity."

        return "This repository has limited community adoption."


#activity method
    @staticmethod
    def activity(score):
        if score >= 80:
            return "Development activity is high."

        if score >= 60:
            return "Reposiotry receives regular updates."

        return "Repository activity is relatively low."


#documentation method
    @staticmethod
    def documentation (score):
        if score >= 90:
            return "Documentation is excellent and comprehensive."

        if score >= 70:
            return "Documentation quality is good."

        if score >= 50:
            return "Documentation is acceptable but could be improved."

        return "Documentation quality is poor."


#maintainability method
    @staticmethod
    def maintainability(score):
        if score >= 90:
            return " Code maintainability is acceptable."

        if score >= 70:
            return "Repository is easy to maintain."

        if score >= 50:
            return "Maintainability is acceptable."

        return "Repository may be difficult to maintain."


#code quality method
    @staticmethod
    def code_quality(score):
        if score >= 90:
            return "Code quality indicators are excellent."

        if  score >= 70:
            return "Community engagement is strong."

        if score >= 50:
            return "Community activity is moderate."

        return "Community engagement is limited."


#community method
    @staticmethod
    def community(score):
        if score >= 90:
            return "Community participation is outstanding."

        if score >= 70:
            return "Community engagement is strong."

        if score >= 50:
            return "Community activity is moderate." 

        return "Community engagement is limited."


#overall method
    @staticmethod
    def overall(score):
        if score >= 90:
            return "Overall repository health is excellent."

        if score >= 80:
            return "Overall repository health is very good." 

        if score >= 70:
            return "Repository quality is good."

        if score >= 50:
            return "Repository quality is average."

        return "Repository requires significant improvements."


#technology method
    @staticmethod
    def technology(technologies):
        if not technologies:
            return None

        main = technologies[0]

        return(
            f"The dominant technology is "
            f"{main['lenguage']} ({main['percentage']}%)."
        )


#project type method
    @staticmethod
    def project_type(project_type):
        return (
            f"The repository is classified as {project_type}"
        )


#production ready method
    @staticmethod
    def production_ready(score):
        if score >= 85:
            return (
                "Repository appears suitable for production environments."
            )

        if score >= 70:
            return (
                "Repository is suitable for the develoment and testing environments."
            )

        return (
            "Repository requires additionnal improvements before production deployment."
        )


#class methods to generate
    @classmethod
    def generate(
        cls,
        repository,
        analysis,
        technologies,
    ):

        insights = [
            cls.popularity(
                analysis.popularity_score
            ),

            cls.activity(
                analysis.activity_score
            ),

            cls.documentation(
                analysis.documentation_score
            ),

            cls.maintainability(
                analysis.maintainability_score
            ),

            cls.code_quality(
                analysis.code_quality_score
            ),

            cls.community(
                analysis.community_score
            ),

            cls.overall(
                analysis.overall_score
            ),

            cls.project_type(
                analysis.project_type_score
            ),

            cls.production_ready(
                analysis.overall_score
            ),
        ]

        technology = cls.technology(
            technologies
        )

        if technology: insights.append(
            technology
        )

        return insights

