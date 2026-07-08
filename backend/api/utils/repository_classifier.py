class RepositoryClassifier:

    @staticmethod
    def classify(name, language, description, topics):

        text = (
            f"{name}"
            f"{language}"
            f"{description}"
            f"{"".join(topics)}"
        )

        if "react" in text:
            return "Frontend"
        
        if "vue" in text:
            return "Frontend"
        
        if "angular" in text:
            return "Frontend"

        if "django" in text:
            return "Backend"
        
        if "flask" in text:
            return "Backend"
        
        if "fastapi" in text:
            return "Backend"

        if "machine learning" in text:
            return "Artificial Intelligence"

        if "tensorflow" in text:
            return "Artificial Intelligence"
        
        if "pytorch" in text:
            return "Artificial Intelligence"
        
        if "docker" in text:
            return "DevOps"

        return "General"