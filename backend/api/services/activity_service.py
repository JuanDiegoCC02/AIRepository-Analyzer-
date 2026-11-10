import math
from datetime import datetime, timezone


class ActivityService:
    """
    Scores how alive a repository is, from 0 to 100.

    Only signals that describe real development work are used. Stars,
    forks and watchers measure popularity, so they are NOT part of this
    score (they already count in the popularity and community scores).

    Signals (maximum points):
      - recency:        how recently code was pushed          (40)
      - commit_volume:  human commits in the last 90 days     (40)
      - active_authors: distinct people who committed         (10)
      - release:        how fresh the latest release is       (10)

    A signal without data is left out and the result is rescaled, so a
    missing piece of information does not unfairly punish a repository.
    """

    RECENCY_MAX = 40
    COMMITS_MAX = 40
    AUTHORS_MAX = 10
    RELEASE_MAX = 10

    # Recency halves every 60 days: 0 days -> 40, 60 -> 20, 120 -> 10...
    RECENCY_HALF_LIFE_DAYS = 60

    # 100 commits (or more) in the window earn the full commit points.
    COMMITS_FOR_FULL_SCORE = 100

    # 5 active authors (or more) earn the full author points.
    AUTHORS_FOR_FULL_SCORE = 5

    RELEASE_FRESH_DAYS = 180
    RELEASE_RECENT_DAYS = 365

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

    @classmethod
    def _days_since(cls, value, now):
        """Days elapsed since an ISO date, or None if it is invalid."""
        parsed = cls._parse_date(value)

        if parsed is None:
            return None

        return max(0.0, (now - parsed).total_seconds() / 86400)

    @staticmethod
    def _non_negative_int(value):
        """Coerce untrusted numeric input into an integer >= 0."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0

        if isinstance(value, float) and not math.isfinite(value):
            return 0

        return max(0, int(value))

    @staticmethod
    def _stats_available(commit_stats):
        return (
            isinstance(commit_stats, dict)
            and commit_stats.get("available") is True
        )

    @classmethod
    def _recency_points(cls, repository, commit_stats, now):
        candidates = [repository.get("pushed_at")]

        if cls._stats_available(commit_stats):
            candidates.append(commit_stats.get("last_commit_at"))

        days = [
            value
            for value in (
                cls._days_since(candidate, now)
                for candidate in candidates
            )
            if value is not None
        ]

        if not days:
            return None

        return cls.RECENCY_MAX * 0.5 ** (
            min(days) / cls.RECENCY_HALF_LIFE_DAYS
        )

    @classmethod
    def _commit_points(cls, commit_stats):
        if not cls._stats_available(commit_stats):
            return None

        commits = cls._non_negative_int(commit_stats.get("commits"))

        # Logarithmic: going from 0 to 10 commits matters more than
        # going from 90 to 100.
        ratio = min(
            1.0,
            math.log1p(commits) / math.log1p(cls.COMMITS_FOR_FULL_SCORE),
        )

        return cls.COMMITS_MAX * ratio

    @classmethod
    def _author_points(cls, commit_stats):
        if not cls._stats_available(commit_stats):
            return None

        authors = cls._non_negative_int(commit_stats.get("active_authors"))

        return cls.AUTHORS_MAX * (
            min(authors, cls.AUTHORS_FOR_FULL_SCORE)
            / cls.AUTHORS_FOR_FULL_SCORE
        )

    @classmethod
    def _release_points(cls, releases, now):
        # Many healthy projects never use GitHub releases, so having none
        # is "no data" (the signal is skipped), not a penalty.
        if not isinstance(releases, dict):
            return None

        latest = releases.get("latest_release")

        if not isinstance(latest, dict):
            return None

        days = cls._days_since(latest.get("published_at"), now)

        if days is None:
            return None

        if days <= cls.RELEASE_FRESH_DAYS:
            return float(cls.RELEASE_MAX)

        if days <= cls.RELEASE_RECENT_DAYS:
            return cls.RELEASE_MAX / 2

        return 0.0

    @classmethod
    def breakdown(
        cls,
        repository,
        commit_stats=None,
        releases=None,
        now=None,
    ):
        """
        Points earned by every signal.

        'points' is None when the signal has no data. This makes the
        score explainable (and useful as input for the AI summary later).
        """
        now = now or datetime.now(timezone.utc)

        if not isinstance(repository, dict):
            repository = {}

        raw = {
            "recency": (
                cls._recency_points(repository, commit_stats, now),
                cls.RECENCY_MAX,
            ),
            "commit_volume": (
                cls._commit_points(commit_stats),
                cls.COMMITS_MAX,
            ),
            "active_authors": (
                cls._author_points(commit_stats),
                cls.AUTHORS_MAX,
            ),
            "release": (
                cls._release_points(releases, now),
                cls.RELEASE_MAX,
            ),
        }

        return {
            name: {
                "points": None if points is None else round(points, 2),
                "max": maximum,
            }
            for name, (points, maximum) in raw.items()
        }

    @classmethod
    def calculate(
        cls,
        repository,
        commit_stats=None,
        releases=None,
        now=None,
    ):
        """
        Return the activity score (integer from 0 to 100).

        'commit_stats' comes from CommitsService and 'releases' from
        ReleaseAnalysisService. Both are optional, so calling
        calculate(github_repository) keeps working.
        """
        if not isinstance(repository, dict):
            return 0

        # An archived repository is read-only: it cannot be active.
        if repository.get("archived"):
            return 0

        signals = cls.breakdown(
            repository,
            commit_stats=commit_stats,
            releases=releases,
            now=now,
        )

        earned = 0.0
        possible = 0

        for signal in signals.values():
            if signal["points"] is None:
                continue

            earned += signal["points"]
            possible += signal["max"]

        if possible == 0:
            return 0

        return max(0, min(100, round(earned / possible * 100)))