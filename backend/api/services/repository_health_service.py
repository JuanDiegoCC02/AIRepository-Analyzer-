


class RepositoryHealthService:

    @staticmethod
    def generate(scores):
        health = {}
        overall = scores["overall_score"]

        if overall >= 90:
            health["status"] = "Excellent"

        elif overall >= 75:
            health["status"] = "Good"

        elif overall >= 60:
            health["status"] = "Fair"

        else: 
            health["status"] = "Poor"

        strengths = []
        weaknesses = []

        if scores["documentation_score"] >= 80:
            strengths.append(
                "Excellent project documentation."
            )
        else: 
            weaknesses.append(
                "Documentation should be improved."
            )

        if scores["activity_score"] >= 80:
            strengths.append(
                "Repository is actively maintained"
            )
        else:
            weaknesses.append(
                "Development activity is low."
            )

        if scores["community_score"] >= 80:
            strengths.append(
                "Strong community engagement."
            )
        else: weaknesses.append(
            "Community engagement is limited"
        )

        if scores["code_quality_score"] >= 80:
            strengths.append(
                'Code quality indicators are strong.'
            )
        else: weaknesses.append(
            "Code quality can be improved."
        )

        health["strengths"] = strengths
        health["weaknesses"] = weaknesses