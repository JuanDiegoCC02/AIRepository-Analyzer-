from datetime import datetime
from django.utils import timezone


class ActivityService:

    @staticmethod
    def calculate(repository):

        score = 0

       
        # Last update
        updated_at = repository.get("updated_at")

        if updated_at:

            updated_date = datetime.fromisoformat(
                updated_at.replace("Z", "+00:00")
            )

            days = (
                timezone.now() - updated_date
            ).days

            if days <= 30:
                score += 40

            elif days <= 90:
                score += 30

            elif days <= 180:
                score += 20

            else:
                score += 10

       
        # Watchers
        watchers = repository.get(
            "watchers_count",
            0,
        )

        if watchers >= 10000:
            score += 20

        elif watchers >= 1000:
            score += 15

        elif watchers >= 100:
            score += 10

       
        # Forks
        forks = repository.get(
            "forks_count",
            0,
        )

        if forks >= 10000:
            score += 20

        elif forks >= 1000:
            score += 15

        elif forks >= 100:
            score += 10

       
        # Open Issues
        issues = repository.get(
            "open_issues_count",
            0,
        )

        if issues <= 100:
            score += 20

        elif issues <= 500:
            score += 15

        elif issues <= 1000:
            score += 10

        else:
            score += 5

        return min(score, 100)