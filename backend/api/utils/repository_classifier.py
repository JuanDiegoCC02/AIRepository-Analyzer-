class RepositoryClassifier:

    @staticmethod
    def classify(name, language, description):

        text = f"{name} {language} {description}".lower()

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