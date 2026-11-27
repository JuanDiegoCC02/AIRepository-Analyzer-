from django.core.management.base import BaseCommand

from api.services.ai_insights_service import AIInsightsService
from api.services.ai_service import AIClient


class Command(BaseCommand):
    help = (
        "Checks the AI summary configuration and makes one real call with "
        "sample data. The API key is never printed."
    )

    def handle(self, *args, **options):
        self.stdout.write(f"Model: {AIClient.model()}")
        self.stdout.write(
            f"API key configured: {'yes' if AIClient.api_key() else 'no'}"
        )
        self.stdout.write(f"AI enabled: {'yes' if AIClient.is_enabled() else 'no'}")

        if not AIClient.is_enabled():
            self.stdout.write(
                self.style.WARNING(
                    "Set AI_SUMMARY_ENABLED=true and ANTHROPIC_API_KEY in .env."
                )
            )
            return

        summary = AIInsightsService.generate(
            {
                "name": "demo-project",
                "description": "A small demo project.",
                "language": "Python",
            },
            "Backend",
            [{"language": "Python", "percentage": 92.5}],
            {
                "overall_score": 74,
                "popularity_score": 55,
                "activity_score": 88,
                "documentation_score": 70,
                "maintainability_score": 81,
                "code_quality_score": 76,
                "community_score": 60,
            },
            None,
        )

        if summary:
            self.stdout.write(self.style.SUCCESS("AI call OK. Summary:"))
            self.stdout.write(summary)
        else:
            self.stdout.write(
                self.style.ERROR(
                    "The AI call failed or was rejected. See the server log."
                )
            )
