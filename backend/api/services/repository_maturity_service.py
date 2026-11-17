import math
from datetime import datetime, timezone


class RepositoryMaturityService:
    ACTIVE_DAYS = 30
    MAINTAINED_DAYS = 180

    @staticmethod
    def _parse_date(value):
        """Parse an ISO 8601 string into an aware UTC datetime."""
        if not isinstance(value, str) or not value:
            return None

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _count(value):
        """Return value as an integer >= 0 (0 when it is not valid)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0

        if isinstance(value, float) and not math.isfinite(value):
            return 0

        return max(0, int(value))

    @classmethod
    def _last_activity(cls, repository, commit_stats):
        """Date of the last real activity, or None when unknown."""
        if isinstance(commit_stats, dict) and commit_stats.get("available"):
            moment = cls._parse_date(commit_stats.get("last_commit_at"))

            if moment is not None:
                return moment

        return cls._parse_date(repository.get("pushed_at"))

    @classmethod
    def calculate(cls, repository, commit_stats=None, now=None):
        if not isinstance(repository, dict):
            repository = {}

        now = now or datetime.now(timezone.utc)

        created = cls._parse_date(repository.get("created_at"))
        last_activity = cls._last_activity(repository, commit_stats)
        archived = repository.get("archived") is True

        years = 0

        if created is not None:
            years = max(0, (now - created).days) // 365

        inactive_days = None

        if last_activity is not None:
            inactive_days = max(0, (now - last_activity).days)

        stars = cls._count(repository.get("stargazers_count"))
        forks = cls._count(repository.get("forks_count"))
        open_issues = repository.get("open_issues_count")

        confidence = 0

        # Age
        if created is not None:
            if years >= 10:
                confidence += 40
            elif years >= 5:
                confidence += 30
            elif years >= 2:
                confidence += 20
            else:
                confidence += 10

        # Stars
        if stars >= 10000:
            confidence += 20
        elif stars >= 1000:
            confidence += 10

        # Forks
        if forks >= 1000:
            confidence += 15
        elif forks >= 100:
            confidence += 10

        # Recent real activity (archived repositories earn nothing here)
        if inactive_days is not None and not archived:
            if inactive_days <= cls.ACTIVE_DAYS:
                confidence += 25
            elif inactive_days <= cls.MAINTAINED_DAYS:
                confidence += 15

        # Manageable amount of open issues
        if (
            not isinstance(open_issues, bool)
            and isinstance(open_issues, int)
            and 0 <= open_issues <= 100
        ):
            confidence += 10

        confidence = min(confidence, 100)

        if confidence >= 90:
            level = "Mature"
        elif confidence >= 75:
            level = "Stable"
        elif confidence >= 55:
            level = "Growing"
        else:
            level = "Early Stage"

        if archived:
            maintenance = "Archived"
        elif inactive_days is None:
            maintenance = "Unknown"
        elif inactive_days <= cls.ACTIVE_DAYS:
            maintenance = "Active"
        elif inactive_days <= cls.MAINTAINED_DAYS:
            maintenance = "Maintained"
        else:
            maintenance = "Inactive"

        if years >= 8:
            stability = "High"
        elif years >= 4:
            stability = "Medium"
        else:
            stability = "Low"

        return {
            "level": level,
            "age_years": years,
            "maintenance": maintenance,
            "stability": stability,
            "confidence": confidence,
            "last_activity_at": (
                last_activity.strftime("%Y-%m-%dT%H:%M:%SZ")
                if last_activity is not None
                else None
            ),
        }
