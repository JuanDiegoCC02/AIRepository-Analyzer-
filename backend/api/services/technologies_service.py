from api.services.github_service import GitHubService



class TechnologiesService:

    @classmethod
    def get_languages(cls, owner, repository):

        endpoint = (
            f"/repos/"
            f"{owner}/"
            f"{repository}/languages"
        )

        try: 
            languages = GitHubService.request(endpoint)

        except Exception:
            return{}

        if not isinstance(languages, dict,):
            return {}

        return languages



    @staticmethod
    def calculate_percentages(languages):

        if not languages:
            return []

        valid_languages = {}

        for language, bytes_count in languages.items():

            if not isinstance(language, str):
                continue

            if not isinstance(bytes_count, int):
                continue

            if bytes_count < 0:
                continue

            total = sum(valid_languages.values())

            if total <= 0:
                return[]

            results = []

            for language, bytes_count in valid_languages.items():

                percentage = round((bytes_count / total) * 100, 2)

                results.append(
                    {
                        "language": language,
                        "bytes": bytes_count,
                        "percentage": percentage,
                    }
                )

                results.sort(
                    key=lambda technology: technology["percentage"],
                    reverse=True
                )

                return results


    
    @staticmethod
    def primary_language(technologies):

        if not technologies:
            return None

        return max(
            technologies,
            key=lambda technology: technology["percentage"],
        )["language"]
    


    @staticmethod
    def get_main_stack(technologies):

        if not technologies:
            return []
        
        return[
            technology["language"]
            for technology in technologies
            if technology ["percentage"] >= 5
        ]



    @classmethod
    def analyze(cls, owner, repository):

        languages = cls.get_languages(
            owner,
            repository,
        )

        technologies = cls.calculate_percentages(languages)

        primary_language = cls.primary_language(technologies)

        main_stack = cls.get_main_stack(technologies)

        return {
            "languages": technologies,
            "primary_language": primary_language,
            "main_stack": main_stack
        }