class DocumentationService:

    @staticmethod
    def calculate(repository):
        score = 0


        # Description
        description = repository.get("description")

        if description:
            score += 20

            if len(description) >= 80:
                score += 10

       
        # Homepage
        homepage = repository.get("homepage")

        if homepage:
            score += 15

        
        # License
        if repository.get("license"):
            score += 15


        # Topics
        topics = repository.get("topics", [])

        if len(topics) >= 5:
            score += 15

        elif len(topics) >= 2:
            score += 10

    
        # Wiki
        if repository.get("has_wiki"):
            score += 10


        # Issues habilitados
        if repository.get("has_issues"):
            score += 5

    
        # Projects habilitados
        if repository.get("has_projects"):
            score += 5

    
        # Discussions
        if repository.get("has_discussions"):
            score += 5

        return min(score, 100)