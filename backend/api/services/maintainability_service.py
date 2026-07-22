class MaintainabilityService:

    @staticmethod
    def calculate(repository):
        score = 0


        # Main language
        language = repository.get("language")

        if language in [
            "Python",
            "JavaScript",
            "TypeScript",
            "Java",
            "C#",
            "Go",
            "Rust",
        ]:
            score += 20

   
        # License
        if repository.get("license"):
            score += 15

       
        # Default branch
        default_branch = repository.get("default_branch")

        if default_branch == "main":
            score += 10

        elif default_branch == "master":
            score += 8

       
        # Forks
        forks = repository.get("forks_count", 0)

        if forks >= 10000:
            score += 20

        elif forks >= 1000:
            score += 15

        elif forks >= 100:
            score += 10

        
        # Open Issues
        issues = repository.get("open_issues_count", 0)

        if issues <= 100:
            score += 15

        elif issues <= 500:
            score += 10

        else:
            score += 5

        
        # Description
        if repository.get("description"):
            score += 10

        
        # Topics
        topics = repository.get("topics", [])

        if len(topics) >= 5:
            score += 10

        return min(score, 100)