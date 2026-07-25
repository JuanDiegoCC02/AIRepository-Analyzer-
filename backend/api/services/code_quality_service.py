class CodeQualityService:

    @staticmethod
    def calculate(repository):

        score = 0

        # Issues
        issues = repository.get(
            "open_issues_count",
            0
        )

        if issues <= 25:
            score += 30

        elif issues <= 100:
            score += 20

        else:
            score += 10

        # Wiki
        if repository.get("has_wiki"):
            score += 10

        # Projects
        if repository.get("has_projects"):
            score += 10

        # Discussions
        if repository.get("has_discussions"):
            score += 10

        # License
        if repository.get("license"):
            score += 20

        # Default Branch
        if repository.get("default_branch") == "main":
            score += 10

        # Archived
        if not repository.get("archived"):
            score += 10

        return min(score, 100)