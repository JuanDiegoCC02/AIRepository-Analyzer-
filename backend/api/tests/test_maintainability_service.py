from django.test import SimpleTestCase

from api.services.maintainability_service import MaintainabilityService


def contributors(*counts, bots=()):
    """Build a contributors summary like ContributorsService returns."""
    entries = [
        {"login": f"person{index}", "contributions": count}
        for index, count in enumerate(counts)
    ]
    entries.extend(
        {"login": login, "contributions": count}
        for login, count in bots
    )

    return {
        "total_contributors": len(entries),
        "capped": False,
        "contributors": entries,
    }


def repository(stars=0, issues=0, **extra):
    data = {"stargazers_count": stars, "open_issues_count": issues}
    data.update(extra)
    return data


def points(result, signal):
    return result[signal]["points"]


# Real data from pallets/flask: davidism made 1865 of 4372 human
# contributions (43%), 97 people contributed, 4 open issues, 75k stars.
FLASK_CONTRIBUTORS = contributors(
    1865,
    1189,
    *([14] * 94 + [2]),
    bots=[("dependabot[bot]", 61), ("pre-commit-ci[bot]", 39)],
)
FLASK = repository(stars=75112, issues=4)


class MaintainabilityServiceTests(SimpleTestCase):

    def test_flask_scores_90(self):
        # bus factor 30 + breadth 25 + backlog 35. The old formula gave
        # 100 for language, license and branch name, which say nothing
        # about how sustainable the project is.
        score = MaintainabilityService.calculate(
            FLASK,
            contributors=FLASK_CONTRIBUTORS,
        )

        self.assertEqual(score, 90)

    def test_score_is_an_integer_between_0_and_100(self):
        score = MaintainabilityService.calculate(
            FLASK,
            contributors=FLASK_CONTRIBUTORS,
        )

        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_maximum_points_add_up_to_100(self):
        result = MaintainabilityService.breakdown(
            FLASK,
            FLASK_CONTRIBUTORS,
        )

        self.assertEqual(
            sum(signal["max"] for signal in result.values()),
            100,
        )

    def test_bus_factor_bands(self):
        cases = [
            ([30, 10, 10, 10, 10, 10, 10, 10], 40),  # 30%
            ([50, 50], 30),                          # 50%
            ([70, 30], 15),                          # 70%
            ([90, 10], 6),                           # 90%
            ([91, 9], 0),                            # 91%
            ([100], 0),                              # one person
        ]

        for counts, expected in cases:
            with self.subTest(counts=counts):
                result = MaintainabilityService.breakdown(
                    repository(),
                    contributors(*counts),
                )

                self.assertEqual(points(result, "bus_factor"), expected)

    def test_bots_are_ignored(self):
        result = MaintainabilityService.breakdown(
            repository(),
            contributors(10, 10, bots=[("dependabot[bot]", 1000)]),
        )

        self.assertEqual(points(result, "bus_factor"), 30)
        self.assertEqual(
            result["bus_factor"]["evidence"],
            ["top contributor made 50% of contributions"],
        )
        self.assertEqual(
            result["contributor_breadth"]["evidence"],
            ["2 human contributors"],
        )

    def test_contributor_breadth_bands(self):
        cases = [(1, 0), (2, 6), (5, 12), (20, 19), (50, 25)]

        for people, expected in cases:
            with self.subTest(people=people):
                result = MaintainabilityService.breakdown(
                    repository(),
                    contributors(*([1] * people)),
                )

                self.assertEqual(
                    points(result, "contributor_breadth"),
                    expected,
                )

    def test_issue_backlog_bands_for_a_small_project(self):
        # With no stars the capacity is the minimum (25 issues).
        cases = [
            (0, 35),
            (12, 35),   # ratio 0.48
            (13, 26),   # ratio 0.52
            (25, 26),   # ratio 1.00
            (26, 15),
            (50, 15),   # ratio 2.00
            (51, 5),
            (5000, 5),
        ]

        for issues, expected in cases:
            with self.subTest(issues=issues):
                result = MaintainabilityService.breakdown(
                    repository(stars=0, issues=issues)
                )

                self.assertEqual(points(result, "issue_backlog"), expected)

    def test_issue_capacity_grows_with_the_stars(self):
        # 100000 stars -> capacity 2000 issues -> 1000 issues is fine.
        popular = MaintainabilityService.breakdown(
            repository(stars=100000, issues=1000)
        )
        small = MaintainabilityService.breakdown(
            repository(stars=100, issues=1000)
        )

        self.assertEqual(points(popular, "issue_backlog"), 35)
        self.assertEqual(points(small, "issue_backlog"), 5)

    def test_invalid_issue_count_is_left_out(self):
        for value in (None, "10", True, float("nan"), [1]):
            with self.subTest(value=value):
                result = MaintainabilityService.breakdown(
                    {"open_issues_count": value}
                )

                self.assertIsNone(points(result, "issue_backlog"))

    def test_missing_contributors_are_left_out_and_score_rescaled(self):
        for value in (None, {}, "text", {"total": 0},
                      {"contributors": []}, {"contributors": "x"}):
            with self.subTest(value=value):
                result = MaintainabilityService.breakdown(
                    repository(),
                    value,
                )

                self.assertIsNone(points(result, "bus_factor"))
                self.assertIsNone(points(result, "contributor_breadth"))
                self.assertEqual(
                    MaintainabilityService.calculate(
                        repository(),
                        value,
                    ),
                    100,
                )

    def test_nothing_to_check_returns_the_neutral_score(self):
        self.assertEqual(
            MaintainabilityService.calculate({}),
            MaintainabilityService.NEUTRAL_SCORE,
        )

    def test_archived_repository_scores_zero(self):
        data = repository(stars=75112, issues=4, archived=True)

        self.assertEqual(
            MaintainabilityService.calculate(
                data,
                FLASK_CONTRIBUTORS,
            ),
            0,
        )

        result = MaintainabilityService.breakdown(
            data,
            FLASK_CONTRIBUTORS,
        )

        for signal in result.values():
            self.assertEqual(signal["points"], 0)

    def test_invalid_repository_scores_zero(self):
        self.assertEqual(MaintainabilityService.calculate(None), 0)
        self.assertEqual(MaintainabilityService.calculate("text"), 0)

    def test_language_license_and_branch_do_not_matter(self):
        base = MaintainabilityService.calculate(
            FLASK,
            FLASK_CONTRIBUTORS,
        )
        noisy = MaintainabilityService.calculate(
            repository(
                stars=75112,
                issues=4,
                language="Python",
                license={"name": "MIT"},
                default_branch="main",
                forks_count=99999,
                description="text",
                topics=["a", "b", "c", "d", "e"],
            ),
            FLASK_CONTRIBUTORS,
        )

        self.assertEqual(base, noisy)

    def test_evidence_never_includes_text_from_github(self):
        result = MaintainabilityService.breakdown(
            repository(),
            {
                "contributors": [
                    {"login": "<script>alert(1)</script>", "contributions": 5},
                    {"login": "../../etc/passwd", "contributions": 5},
                ]
            },
        )

        for signal in result.values():
            for line in signal["evidence"]:
                self.assertNotIn("<script>", line)
                self.assertNotIn("passwd", line)

    def test_malformed_contributor_entries_do_not_crash(self):
        result = MaintainabilityService.breakdown(
            repository(),
            {
                "contributors": [
                    None, "text", 5, {"login": 7, "contributions": "x"},
                    {"login": "a", "contributions": -3},
                    {"login": "b", "contributions": True},
                    {"login": "c", "contributions": 4},
                ]
            },
        )

        self.assertEqual(points(result, "contributor_breadth"), 0)
        self.assertEqual(points(result, "bus_factor"), 0)
