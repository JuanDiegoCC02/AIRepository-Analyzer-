class RepositoryClassifier:

    CATEGORIES = {
        "Frontend": [
            "react",
            "vue",
            "angular",
            "svelte",
            "next",
            "nuxt",
            "vite",
        ],

        "Backend": [
            "django",
            "flask",
            "fastapi",
            "spring",
            "express",
            "laravel",
            "node",
        ],

        "Artificial Intelligence": [
            "machine learning",
            "deep learning",
            "tensorflow",
            "pytorch",
            "keras",
            "huggingface",
            "llm",
            "transformers",
        ],

        "DevOps": [
            "docker",
            "kubernetes",
            "terraform",
            "ansible",
            "jenkins",
            "github actions",
        ],

        "Mobile": [
            "flutter",
            "android",
            "ios",
            "swift",
            "kotlin",
            "react native",
        ],

        "Data Science": [
            "pandas",
            "numpy",
            "matplotlib",
            "scikit",
            "jupyter",
        ],
    }

    @classmethod
    def classify(cls, name, language, description, topics):

        text = " ".join([
            name or "",
            language or "",
            description or "",
            " ".join(topics or [])
        ]).lower()

        for category, keywords in cls.CATEGORIES.items():

            for keyword in keywords:

                if keyword in text:
                    return category

        return "General"