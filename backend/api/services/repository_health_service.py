import math


class RepositoryHealthService:
    STRENGTH_SCORE = 80
    WEAKNESS_SCORE = 60

    # (score key, strength message, weakness message)
    DIMENSIONS = [
        (
            "documentation_score",
            "Excellent project documentation.",
            "Documentation should be improved.",
        ),
        (
            "activity_score",
            "Repository is actively maintained.",
            "Development activity is low.",
        ),
        (
            "community_score",
            "Strong community engagement.",
            "Community engagement is limited.",
        ),
        (
            "code_quality_score",
            "Code quality indicators are strong.",
            "Code quality can be improved.",
        ),
    ]

    @staticmethod
    def _number(value):
        """Return value as a number, or 0 if it is not a valid score."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0

        if not math.isfinite(value):
            return 0

        return value

    @classmethod
    def generate(cls, scores):
        """Generate health status, strengths, and weaknesses."""
        if not isinstance(scores, dict):
            scores = {}

        overall = cls._number(scores.get("overall_score", 0))

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

        for key, strength, weakness in cls.DIMENSIONS:
            score = cls._number(scores.get(key, 0))

            if score >= cls.STRENGTH_SCORE:
                strengths.append(strength)
            elif score < cls.WEAKNESS_SCORE:
                weaknesses.append(weakness)

        return {
            "status": status,
            "overall_score": overall,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }