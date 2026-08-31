


class RepositoryTopicsService:
    def analyze(topics):

        if not topics:
            return{
                "frameworks": ["not found"],
                "domains": ["not found"],
                "tools": ["not found"],
                "other": ["not found"],
            }

        frameworks = []
        domains = []
        tools = []
        other = []

        framework_keywords = {
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
            "spring",
            "laravel",
            "nextjs",
            "nuxt",
        } 

        domain_keywords = {
            "machine-learning",
            "artificial-intelligence",
            "nlp",
            "computer-vision",
            "frontend",
            "backend",
            "mobile",
            "web",
            "api",
            "rest-api",
            "microservices",
            "iot",
            "telecommunications",
        }

        tool_keywords = {
            "docker",
            "kubernetes",
            "terraform",
            "aws",
            "azure",
            "gcp",
            "postgresql",
            "mysql",
            "redis",
            "mongodb",
            "graphql",
            "vite",
            "webpack",
        }

        for topic in topics:
            value = topic.lower()

            if value in framework_keywords:
                frameworks.append(topic)

            elif value in domain_keywords:
                domains.append(topic)

            elif value in tool_keywords:
                tools.append(topic)

            else: 
                other.append(topic)

        return {
            "frameworks": frameworks,
            "domains": domains,
            "tools": tools,
            "other": other,
        }