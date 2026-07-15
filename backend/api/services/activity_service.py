from datetime import datetime, timezone


class ActivityService:

    @staticmethod
    def calculate(repository):

        updated_at = repository.get("updated_at")

        updated = datetime.fromisoformat(
            updated_at.replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)

        days = (now - updated).days

        if days <= 7:
            return 100

        if days <= 30:
            return 80

        if days <= 90:
            return 60

        if days <= 180:
            return 40

        return 20