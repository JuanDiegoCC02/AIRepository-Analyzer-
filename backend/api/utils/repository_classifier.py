class RepositoryClassifier:

    @staticmethod
    def classify(language, description):

        text = f"{language} {description}".lower()

        if "react" in text:

            return "Frontend"

        if "django" in text:

            return "Backend"

        if "machine learning" in text:

            return "Artificial Intelligence"

        if "tensorflow" in text:

            return "Artificial Intelligence"

        return "General"