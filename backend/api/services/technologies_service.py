from api.services.github_service import GitHubService


class TechnologiesService:

    """
    Service responsible for retrieving and analtzing programming languages 
    used by a GitHub repository.
    """

    @classmethod
    def get_languages(cls, owner, repository):

        """
        Retrieves the programming languages used by a GitHub repository.
        GitHub communication is delegated to GitHubService
        """

        endpoint = (
            f"/repos/"
            f"{owner}/"
            f"{repository}/languages"
        )

        try: 
            languages = GitHubService.request(endpoint)
        except Exception:
            return{}

        if not isinstance(
            languages,
            dict
        ):
            return {}

        return languages



    @staticmethod
    def calculate_percentages(languages):

        total = sum(languages.values())

        if total == 0:
            return []

        results = []

        for language, bytes_count in languages.items():

            percentage = round(
                (bytes_count / total) * 100,
                2
            )

            results.append({
                "language": language,
                "bytes": bytes_count,
                "percentage": percentage
            })

        return results
    


    @staticmethod
    def primary_language(technologies):

        if not technologies:
            return None

        return max(
            technologies,
            key=lambda technology: technology["percentage"]
        )["language"]
    


    @staticmethod
    def get_main_stack(technologies):
        
        return[
            technology["language"]
            for technology in technologies
            if technology ["percentage"] >=5
        ]