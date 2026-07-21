import requests


class TechnologiesService:
    BASE_URL = "https://api.github.com/repos"

    @classmethod
    def get_languages(cls, owner, repository):

        url = f"{cls.BASE_URL}/{owner}/{repository}/languages"

        response = requests.get(url)

        print("=" * 50)
        print("URL:", url)
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        print("=" * 50)

        if response.status_code == 404:
            raise Exception("Repository languages not found.")

        if response.status_code != 200:
            raise Exception(
                f"GitHub API returned {response.status_code}"
            )

        return response.json()



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