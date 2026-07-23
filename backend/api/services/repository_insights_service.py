class RepositoryInsightsService:

    @staticmethod
    def generate(
        repository,
        analysis,
        technologies,
    ):

        insights = []

        # Popularidad
        if analysis.popularity_score >= 90:
            insights.append(
                "This repository is highly popular within the GitHub community."
            )

        elif analysis.popularity_score >= 70:
            insights.append(
                "This repository has a solid community adoption."
            )

        else:
            insights.append(
                "This repository has limited community adoption."
            )

        # Actividad

        if analysis.activity_score >= 80:
            insights.append(
                "Development activity is high."
            )

        else:
            insights.append(
                "Repository activity is relatively low."
            )

        # Tecnologías
        if technologies:

            main = technologies[0]

            insights.append(
                f"The main technology is {main['language']} ({main['percentage']}%)."
            )

        # Tipo

        insights.append(
            f"The repository is classified as {analysis.project_type}."
        )

        return insights