


class RepositoryHealthService:
    """Evaluates repository health using analysis scores."""

    @staticmethod
    def generate(scores):
        """Generate health status, strengths, and weaknesses."""
        scores = scores or {}

        overall = scores.get("overall_score", 0)
        documentation = scores.get("documentation_score", 0)
        activity = scores.get("activity_score", 0)
        community = scores.get("community_score", 0)
        code_quality = scores.get("code_quality_score", 0)

        if overall >= 90:
            status = "Excellent"
        elif overall >= 75:
            status = "Good"
        elif overall >= 60:
            status = "Fair"
        else:
            status = "Poor"

        strengths = []
        weaknesses = []

        if documentation >= 80:
            strengths.append("Excellent project documentation.")
        else:
            weaknesses.append("Documentation should be improved.")

        if activity >= 80:
            strengths.append("Repository is actively maintained.")
        else:
            weaknesses.append("Development activity is low.")

        if community >= 80:
            strengths.append("Strong community engagement.")
        else:
            weaknesses.append("Community engagement is limited.")

        if code_quality >= 80:
            strengths.append("Code quality indicators are strong.")
        else:
            weaknesses.append("Code quality can be improved.")

        return {
            "status": status,
            "overall_score": overall,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }
