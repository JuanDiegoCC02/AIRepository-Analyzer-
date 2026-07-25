


class CommunityService:

    @staticmethod
    def calculate(repository):

        score = 0

        stars = repository.get(
            "stargazers_count",
            0,
        )

        forks = repository.get(
            "forks_count",
            0,
        )

        watchers = repository.get(
            "watchers_count",
            0,
        )

        issues = repository.get(
            "open_issues_count",
            0,
        )

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

        # Watchers

        if watchers >= 10000:
            score += 20

        elif watchers >= 1000:
            score += 15

        elif watchers >= 100:
            score += 10

        # Issues

        if issues <= 100:
            score += 15

        elif issues <= 500:
            score += 10

        return min(score, 100)