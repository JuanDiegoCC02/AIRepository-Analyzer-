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

        """
        Calculates the percentage of each programming language based on the number 
        of bytes reported by GitHub.
        """

        if not languages:
            return []

        total = sum( languages.values() )

        if total <= 0:
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
                "percentage": percentage,
            })

        results.sort(
            key=lambda technology: technology["percentage"],
            reverse=True
        )

        return results

    

    @staticmethod
    def primary_language(technologies):

        """
        Returns the programming language with the highest percentage.
        """

        if not technologies:
            return None

        return max(
            technologies,
            key=lambda technology: technology["percentage"],
        )["language"]
    


    @staticmethod
    def get_main_stack(technologies):

        """
        Returns programming languages representing at least 5% of the repository codebase.
        """

        if not technologies:
            return []
        
        return[
            technology["language"]
            for technology in technologies
            if technology ["percentage"] >=5
        ]

    @classmethod
    def analyze(cls, owner, repository):

        """
        Complete technology analysis pipeline:
        1 Retrieves language statistics from GitHub.
        2 Calculates language percentages.
        3 Determines the primary language.
        4 Determines the main technology stack.
        """

        languages = cls.get_languages(
            owner,
            repository,
        )

        technolohies = cls.calculate_percentages(languages)

        primary_language = cls.primary_language(technolohies)

        main_stack = cls.get_main_stack(technolohies)

        return {
            "languages": technolohies,
            "primary_language": primary_language,
            "main_stack": main_stack
        }