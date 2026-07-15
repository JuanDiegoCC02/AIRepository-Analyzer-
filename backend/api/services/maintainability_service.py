


class MaintainabilityService:

    @staticmethod
    def calculate(repository):

        score = 50

        language = repository.get("language")

        stars = repository.get("stargazers_count", 0)

        forks = repository.get("forks_count", 0)

        issues = repository.get("open_issues_count", 0)

        license = repository.get("license")

        if language in [
            "Python",
            "JavaScript",
            "TypeScript",
            "Java",
            "C#",
            "Go",
            "Rust",
        ]:
            score += 15

        if stars >= 1000:
            score += 10

        if forks >= 100:
            score += 10

        if issues <= 100:
            score += 15

        if license:
            score += 10

        return min(score, 100)