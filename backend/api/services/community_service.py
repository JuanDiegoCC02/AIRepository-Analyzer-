import math


class CommunityService:

    @staticmethod
    def _count(value):
        """Return value as an integer >= 0 (0 when it is not valid)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0

        if isinstance(value, float) and not math.isfinite(value):
            return 0

        return max(0, int(value))

    @classmethod
    def calculate(cls, repository):

        if not isinstance(repository, dict):
            return 0

        score = 0

        stars = cls._count(repository.get("stargazers_count"))
        forks = cls._count(repository.get("forks_count"))
        subscribers = cls._count(repository.get("subscribers_count"))
        issues = repository.get("open_issues_count")

        # Stars

        if stars >= 100000:
            score += 40

        elif stars >= 10000:
            score += 30

        elif stars >= 1000:
            score += 20

        else:
            score += 10

        # Forks

        if forks >= 10000:
            score += 25

        elif forks >= 1000:
            score += 20

        elif forks >= 100:
            score += 10

        # Subscribers (people following the repository)

        if subscribers >= 1000:
            score += 20

        elif subscribers >= 300:
            score += 15

        elif subscribers >= 50:
            score += 10

        # Issues (only when GitHub reported them)

        if isinstance(issues, int) and not isinstance(issues, bool):
            if 0 <= issues <= 100:
                score += 15

            elif issues <= 500:
                score += 10

        return min(score, 100)
