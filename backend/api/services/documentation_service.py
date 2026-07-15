


class DocumentationService:

    @staticmethod
    def calculate(repository):

        score = 0

        description = repository.get("description")
        homepage = repository.get("homepage")

        if description:
            score += 40

        if homepage:
            score += 30

        if description and len(description) >= 80:
            score += 30

        return min(score, 100)