import math


class MaintainabilityService:
    BUS_FACTOR_MAX = 40
    BREADTH_MAX = 25
    BACKLOG_MAX = 35

    NEUTRAL_SCORE = 50

    # Issue capacity: a project is expected to handle one open issue per
    # STARS_PER_ISSUE_SLOT stars, with a minimum so small projects are not
    # punished for having a handful of issues.
    STARS_PER_ISSUE_SLOT = 50
    MIN_CAPACITY = 25

    # (maximum share of the top contributor, points)
    BUS_FACTOR_BANDS = (
        (0.30, 40),
        (0.50, 30),
        (0.70, 15),
        (0.90, 6),
    )

    # (minimum number of human contributors, points)
    BREADTH_BANDS = (
        (50, 25),
        (20, 19),
        (5, 12),
        (2, 6),
    )

    # (maximum open issues / capacity, points)
    BACKLOG_BANDS = (
        (0.5, 35),
        (1.0, 26),
        (2.0, 15),
    )
    BACKLOG_WORST_POINTS = 5

    @staticmethod
    def _count(value):
        """Return value as an integer >= 0, or None if it is not valid."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        if isinstance(value, float) and not math.isfinite(value):
            return None

        return max(0, int(value))

    @classmethod
    def _human_contributions(cls, contributors):
        """
        Return the contribution counts of the human contributors, or None
        when there is no usable contributor data.

        `contributors` is the summary built by ContributorsService.
        """
        if not isinstance(contributors, dict):
            return None

        entries = contributors.get("contributors")

        if not isinstance(entries, list):
            return None

        counts = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            login = entry.get("login")

            if isinstance(login, str) and login.lower().endswith("[bot]"):
                continue

            contributions = cls._count(entry.get("contributions"))

            if contributions:
                counts.append(contributions)

        return counts or None

    @staticmethod
    def _signal(points, maximum, evidence=None):
        return {
            "points": points,
            "max": maximum,
            "evidence": evidence or [],
        }

    @classmethod
    def _bus_factor(cls, counts):
        if counts is None:
            return cls._signal(None, cls.BUS_FACTOR_MAX)

        share = max(counts) / sum(counts)

        points = 0

        for limit, band_points in cls.BUS_FACTOR_BANDS:
            if share <= limit:
                points = band_points
                break

        return cls._signal(
            points,
            cls.BUS_FACTOR_MAX,
            [f"top contributor made {round(share * 100)}% of contributions"],
        )

    @classmethod
    def _breadth(cls, counts):
        if counts is None:
            return cls._signal(None, cls.BREADTH_MAX)

        points = 0

        for minimum, band_points in cls.BREADTH_BANDS:
            if len(counts) >= minimum:
                points = band_points
                break

        return cls._signal(
            points,
            cls.BREADTH_MAX,
            [f"{len(counts)} human contributors"],
        )

    @classmethod
    def _backlog(cls, repository):
        issues = cls._count(repository.get("open_issues_count"))

        if issues is None:
            return cls._signal(None, cls.BACKLOG_MAX)

        stars = cls._count(repository.get("stargazers_count")) or 0

        capacity = max(
            cls.MIN_CAPACITY,
            stars / cls.STARS_PER_ISSUE_SLOT,
        )

        ratio = issues / capacity

        points = cls.BACKLOG_WORST_POINTS

        for limit, band_points in cls.BACKLOG_BANDS:
            if ratio <= limit:
                points = band_points
                break

        return cls._signal(
            points,
            cls.BACKLOG_MAX,
            [f"{issues} open issues or pull requests"],
        )

    @classmethod
    def breakdown(cls, repository, contributors=None):
        """Return the points earned by each signal (None = no data)."""
        if not isinstance(repository, dict):
            repository = {}

        counts = cls._human_contributions(contributors)

        signals = {
            "bus_factor": cls._bus_factor(counts),
            "contributor_breadth": cls._breadth(counts),
            "issue_backlog": cls._backlog(repository),
        }

        if repository.get("archived") is True:
            for signal in signals.values():
                if signal["points"] is not None:
                    signal["points"] = 0

            signals["issue_backlog"]["evidence"] = ["repository is archived"]

        return signals

    @classmethod
    def calculate(cls, repository, contributors=None):
        """Return the maintainability score as an integer from 0 to 100."""
        if not isinstance(repository, dict):
            return 0

        if repository.get("archived") is True:
            return 0

        signals = cls.breakdown(repository, contributors)

        earned = 0
        possible = 0

        for signal in signals.values():
            if signal["points"] is None:
                continue

            earned += signal["points"]
            possible += signal["max"]

        if possible == 0:
            return cls.NEUTRAL_SCORE

        return max(0, min(100, round(earned / possible * 100)))
