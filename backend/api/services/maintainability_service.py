


class MaintainabilityService:

    @staticmethod
    def calculate(language, stars, forks, open_issues):

        score = 50

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

        if open_issues <= 100:
            score += 15

        if score > 100:
            score = 100

        return score