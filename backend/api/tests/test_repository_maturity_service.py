from datetime import datetime, timedelta, timezone

from django.test import SimpleTestCase

from api.services.repository_maturity_service import (
    RepositoryMaturityService,
)

NOW = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def days_ago(days):
    return iso(NOW - timedelta(days=days))


def commits(days=3):
    return {"available": True, "last_commit_at": days_ago(days)}


# Real data from pallets/flask.
FLASK = {
    "created_at": "2010-04-06T11:11:59Z",
    "updated_at": "2026-11-15T10:00:00Z",
    "stargazers_count": 75112,
    "forks_count": 17323,
    "open_issues_count": 4,
}

SMALL = {
    "created_at": days_ago(365),
    "stargazers_count": 5,
    "forks_count": 0,
    "open_issues_count": 10,
}


def calculate(repository, commit_stats=None):
    return RepositoryMaturityService.calculate(
        repository,
        commit_stats=commit_stats,
        now=NOW,
    )


class RepositoryMaturityServiceTests(SimpleTestCase):

    def test_flask_is_mature_and_active(self):
        result = calculate(
            FLASK,
            {"available": True, "last_commit_at": "2026-10-30T15:05:20Z"},
        )

        self.assertEqual(result["level"], "Mature")
        self.assertEqual(result["confidence"], 100)
        self.assertEqual(result["age_years"], 16)
        self.assertEqual(result["stability"], "High")
        self.assertEqual(result["maintenance"], "Active")
        self.assertEqual(result["last_activity_at"], "2026-10-30T15:05:20Z")

    def test_updated_at_is_not_used_to_measure_maintenance(self):
        # GitHub changes updated_at when someone stars or comments, so a
        # project without commits for a year must not look active.
        data = dict(FLASK, updated_at=days_ago(1))

        result = calculate(data, commits(days=400))

        self.assertEqual(result["maintenance"], "Inactive")

    def test_maintenance_bands(self):
        cases = [
            (0, "Active"),
            (30, "Active"),
            (31, "Maintained"),
            (180, "Maintained"),
            (181, "Inactive"),
        ]

        for days, expected in cases:
            with self.subTest(days=days):
                result = calculate(FLASK, commits(days))

                self.assertEqual(result["maintenance"], expected)

    def test_falls_back_to_pushed_at_without_commit_data(self):
        data = dict(FLASK, pushed_at=days_ago(100))

        for stats in (None, {"available": False}, {}):
            with self.subTest(stats=stats):
                result = calculate(data, stats)

                self.assertEqual(result["maintenance"], "Maintained")
                self.assertEqual(
                    result["last_activity_at"],
                    days_ago(100),
                )

    def test_falls_back_to_pushed_at_when_no_recent_commit_is_known(self):
        data = dict(FLASK, pushed_at=days_ago(100))

        result = calculate(
            data,
            {"available": True, "last_commit_at": None},
        )

        self.assertEqual(result["maintenance"], "Maintained")

    def test_unknown_activity(self):
        result = calculate(FLASK)

        self.assertEqual(result["maintenance"], "Unknown")
        self.assertIsNone(result["last_activity_at"])

    def test_archived_repository_is_labelled_archived(self):
        result = calculate(dict(FLASK, archived=True), commits(1))

        self.assertEqual(result["maintenance"], "Archived")

    def test_archived_repository_earns_no_activity_points(self):
        active = calculate(FLASK, commits(1))
        archived = calculate(dict(FLASK, archived=True), commits(1))

        self.assertEqual(active["confidence"], 100)
        self.assertEqual(archived["confidence"], 85)

    def test_young_small_repository_is_early_stage(self):
        # age 10 + stars 0 + forks 0 + activity 25 + issues 10 = 45
        result = calculate(SMALL, commits(3))

        self.assertEqual(result["confidence"], 45)
        self.assertEqual(result["level"], "Early Stage")
        self.assertEqual(result["stability"], "Low")
        self.assertEqual(result["age_years"], 1)

    def test_growing_level(self):
        # age 20 + stars 10 + forks 10 + maintained 15 = 55 (no issue data)
        data = {
            "created_at": days_ago(3 * 365),
            "stargazers_count": 1000,
            "forks_count": 100,
        }

        result = calculate(data, commits(100))

        self.assertEqual(result["confidence"], 55)
        self.assertEqual(result["level"], "Growing")

    def test_stable_level(self):
        # age 20 + stars 10 + forks 10 + active 25 + issues 10 = 75
        data = {
            "created_at": days_ago(3 * 365),
            "stargazers_count": 1000,
            "forks_count": 100,
            "open_issues_count": 5,
        }

        result = calculate(data, commits(3))

        self.assertEqual(result["confidence"], 75)
        self.assertEqual(result["level"], "Stable")

    def test_stability_depends_on_age(self):
        cases = [(1, "Low"), (4, "Medium"), (8, "High")]

        for years, expected in cases:
            with self.subTest(years=years):
                data = dict(SMALL, created_at=days_ago(years * 365 + 5))

                self.assertEqual(
                    calculate(data)["stability"],
                    expected,
                )

    def test_missing_or_invalid_data_does_not_crash(self):
        for value in ({}, None, "text", 5, [], {"created_at": "bad"}):
            with self.subTest(value=value):
                result = calculate(value)

                self.assertEqual(result["level"], "Early Stage")
                self.assertEqual(result["confidence"], 0)
                self.assertEqual(result["maintenance"], "Unknown")
                self.assertEqual(result["age_years"], 0)

    def test_invalid_numbers_count_as_zero(self):
        data = {
            "created_at": days_ago(365),
            "stargazers_count": "many",
            "forks_count": None,
            "open_issues_count": True,
        }

        # Only the age points (10) are earned.
        self.assertEqual(calculate(data)["confidence"], 10)

    def test_future_dates_do_not_produce_negative_values(self):
        data = dict(
            SMALL,
            created_at=iso(NOW + timedelta(days=30)),
        )

        result = calculate(data, commits(days=-5))

        self.assertEqual(result["age_years"], 0)
        self.assertEqual(result["maintenance"], "Active")

    def test_confidence_never_exceeds_100(self):
        result = calculate(FLASK, commits(1))

        self.assertLessEqual(result["confidence"], 100)
