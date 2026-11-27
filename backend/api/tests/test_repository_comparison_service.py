import copy
from unittest.mock import patch

from django.test import SimpleTestCase

from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from api.services.repository_comparison_service import (
    RepositoryComparisonService,
)

ANALYZE = (
    "api.services.repository_comparison_service."
    "AnalyzerService.analyze_repository"
)

DIMENSIONS = (
    "popularity",
    "activity",
    "documentation",
    "maintainability",
    "code_quality",
    "community",
)


def result(
    name,
    scores=None,
    project_type="Backend",
    complete=True,
    missing=(),
    version=5,
    **overrides,
):
    """Build the part of an AnalyzerService result that is compared."""
    values = {dimension: 70 for dimension in DIMENSIONS}
    values["overall"] = 70
    values.update(scores or {})

    analysis = {
        "id": hash(name) % 1000,
        "score_version": version,
    }
    analysis.update({f"{key}_score": value for key, value in values.items()})

    data = {
        "repository": {
            "id": abs(hash(name)) % 1000,
            "full_name": name,
            "html_url": f"https://github.com/{name}",
            "description": f"{name} description",
            "language": "Python",
            "stars": 10,
            "forks": 2,
        },
        "analysis": analysis,
        "analysis_result": {
            "overall": {"score": values["overall"], "level": "Good"},
        },
        "classification": {"project_type": project_type},
        "data_quality": {"complete": complete, "missing": list(missing)},
    }
    data.update(overrides)
    return data


def compare(*results):
    return RepositoryComparisonService.compare(list(results))


class RankingTests(SimpleTestCase):

    def test_clear_winner_and_margin(self):
        comparison = compare(
            result("a/one", {"activity": 90}),
            result("b/two", {"activity": 60}),
        )

        activity = comparison["dimensions"]["activity"]

        self.assertEqual(activity["winner"], "a/one")
        self.assertEqual(activity["leaders"], ["a/one"])
        self.assertEqual(activity["margin"], 30)
        self.assertEqual(activity["verdict"], "clear")
        self.assertEqual(
            activity["scores"],
            [
                {"repository": "a/one", "score": 90},
                {"repository": "b/two", "score": 60},
            ],
        )

    def test_verdict_depends_on_the_margin(self):
        cases = [(75, "clear"), (74, "close"), (71, "close")]

        for score, expected in cases:
            with self.subTest(score=score):
                comparison = compare(
                    result("a/one", {"activity": score}),
                    result("b/two", {"activity": 70}),
                )

                ranking = comparison["dimensions"]["activity"]

                self.assertEqual(ranking["verdict"], expected)
                self.assertEqual(ranking["winner"], "a/one")

    def test_a_tie_has_no_winner(self):
        comparison = compare(
            result("a/one", {"activity": 80}),
            result("b/two", {"activity": 80}),
        )

        activity = comparison["dimensions"]["activity"]

        self.assertIsNone(activity["winner"])
        self.assertEqual(activity["leaders"], ["a/one", "b/two"])
        self.assertEqual(activity["margin"], 0)
        self.assertEqual(activity["verdict"], "tie")

    def test_three_repositories_margin_is_against_the_second_best(self):
        comparison = compare(
            result("a/one", {"community": 60}),
            result("b/two", {"community": 90}),
            result("c/three", {"community": 80}),
        )

        community = comparison["dimensions"]["community"]

        self.assertEqual(community["winner"], "b/two")
        self.assertEqual(community["margin"], 10)

    def test_tie_between_the_best_two_of_three(self):
        comparison = compare(
            result("a/one", {"community": 90}),
            result("b/two", {"community": 90}),
            result("c/three", {"community": 50}),
        )

        community = comparison["dimensions"]["community"]

        self.assertIsNone(community["winner"])
        self.assertEqual(community["leaders"], ["a/one", "b/two"])
        self.assertEqual(community["verdict"], "tie")

    def test_invalid_scores_are_left_out_of_the_ranking(self):
        for bad in (None, True, "90", float("nan"), -1, 101):
            with self.subTest(bad=bad):
                comparison = compare(
                    result("a/one", {"activity": bad}),
                    result("b/two", {"activity": 60}),
                    result("c/three", {"activity": 50}),
                )

                activity = comparison["dimensions"]["activity"]

                self.assertEqual(activity["winner"], "b/two")
                self.assertEqual(activity["margin"], 10)
                self.assertIsNone(activity["scores"][0]["score"])

    def test_fewer_than_two_valid_scores_cannot_be_compared(self):
        comparison = compare(
            result("a/one", {"activity": None}),
            result("b/two", {"activity": 60}),
        )

        activity = comparison["dimensions"]["activity"]

        self.assertEqual(activity["verdict"], "unknown")
        self.assertIsNone(activity["winner"])
        self.assertEqual(activity["leaders"], [])

    def test_overall_is_ranked_separately(self):
        comparison = compare(
            result("a/one", {"overall": 88}),
            result("b/two", {"overall": 70}),
        )

        self.assertEqual(comparison["overall"]["winner"], "a/one")
        self.assertEqual(comparison["overall"]["margin"], 18)
        self.assertNotIn("overall", comparison["dimensions"])
        self.assertEqual(set(comparison["dimensions"]), set(DIMENSIONS))


class SummaryTests(SimpleTestCase):

    def test_wins_count_only_the_dimension_winners(self):
        comparison = compare(
            result("a/one", {"popularity": 90, "activity": 90,
                             "documentation": 60, "community": 70}),
            result("b/two", {"popularity": 50, "activity": 50,
                             "documentation": 80, "community": 70}),
        )

        # Four dimensions are left at 70/70 (ties): nobody wins them.
        self.assertEqual(
            comparison["summary"]["wins"],
            {"a/one": 2, "b/two": 1},
        )

    def test_best_overall_and_verdict(self):
        comparison = compare(
            result("a/one", {"overall": 80}),
            result("b/two", {"overall": 78}),
        )

        self.assertEqual(comparison["summary"]["best_overall"], "a/one")
        self.assertEqual(comparison["summary"]["overall_verdict"], "close")

    def test_no_best_overall_when_tied(self):
        comparison = compare(result("a/one"), result("b/two"))

        self.assertIsNone(comparison["summary"]["best_overall"])
        self.assertEqual(comparison["summary"]["overall_verdict"], "tie")

    def test_score_version_is_reported_when_shared(self):
        comparison = compare(result("a/one"), result("b/two"))

        self.assertEqual(comparison["score_version"], 5)

    def test_repository_entries_summarize_each_analysis(self):
        comparison = compare(
            result("a/one", {"activity": 90}),
            result("b/two"),
        )

        entry = comparison["repositories"][0]

        self.assertEqual(entry["full_name"], "a/one")
        self.assertEqual(entry["html_url"], "https://github.com/a/one")
        self.assertEqual(entry["level"], "Good")
        self.assertEqual(entry["project_type"], "Backend")
        self.assertEqual(entry["score_version"], 5)
        self.assertEqual(entry["scores"]["activity"], 90)
        self.assertEqual(entry["scores"]["overall"], 70)
        self.assertTrue(entry["data_complete"])
        self.assertEqual(entry["missing_data"], [])
        self.assertEqual(
            set(entry["scores"]),
            set(DIMENSIONS) | {"overall"},
        )


class HighlightTests(SimpleTestCase):

    def test_clear_differences_are_highlighted(self):
        comparison = compare(
            result("a/one", {"overall": 90, "activity": 95,
                             "documentation": 72}),
            result("b/two", {"overall": 70, "activity": 60,
                             "documentation": 70}),
        )

        self.assertEqual(
            comparison["highlights"],
            [
                "a/one has the highest overall score, 20 points ahead.",
                "a/one leads in development activity by 35 points.",
            ],
        )

    def test_close_overall_is_described_as_slightly_ahead(self):
        comparison = compare(
            result("a/one", {"overall": 73}),
            result("b/two", {"overall": 70}),
        )

        self.assertEqual(
            comparison["highlights"],
            ["a/one is slightly ahead overall (3 points)."],
        )

    def test_one_point_is_singular(self):
        comparison = compare(
            result("a/one", {"overall": 71}),
            result("b/two", {"overall": 70}),
        )

        self.assertEqual(
            comparison["highlights"],
            ["a/one is slightly ahead overall (1 point)."],
        )

    def test_tie_is_highlighted(self):
        comparison = compare(result("a/one"), result("b/two"))

        self.assertEqual(
            comparison["highlights"],
            ["The repositories are tied overall."],
        )


class WarningTests(SimpleTestCase):

    def test_no_warnings_for_comparable_repositories(self):
        comparison = compare(result("a/one"), result("b/two"))

        self.assertEqual(comparison["warnings"], [])

    def test_incomplete_data_is_reported(self):
        comparison = compare(
            result("a/one", complete=False, missing=["commits", "structure"]),
            result("b/two"),
        )

        self.assertEqual(
            comparison["warnings"],
            [
                "GitHub could not provide commits, structure for a/one: "
                "its scores may not be fully comparable."
            ],
        )
        self.assertFalse(comparison["repositories"][0]["data_complete"])
        self.assertEqual(
            comparison["repositories"][0]["missing_data"],
            ["commits", "structure"],
        )

    def test_different_project_types_are_reported_in_order(self):
        comparison = compare(
            result("a/one", project_type="Frontend"),
            result("b/two", project_type="Backend"),
        )

        self.assertEqual(
            comparison["warnings"],
            [
                "The repositories have different project types "
                "(Backend, Frontend), so the comparison may be less "
                "meaningful."
            ],
        )

    def test_different_score_versions_are_reported(self):
        comparison = compare(
            result("a/one", version=5),
            result("b/two", version=4),
        )

        self.assertIsNone(comparison["score_version"])
        self.assertEqual(len(comparison["warnings"]), 1)
        self.assertIn("different score versions", comparison["warnings"][0])


class RobustnessTests(SimpleTestCase):

    def test_malformed_results_do_not_crash(self):
        comparison = RepositoryComparisonService.compare(
            [None, {}, "text", {"analysis": None, "repository": 5}]
        )

        self.assertEqual(len(comparison["repositories"]), 4)

        for ranking in comparison["dimensions"].values():
            self.assertEqual(ranking["verdict"], "unknown")

        self.assertEqual(comparison["overall"]["verdict"], "unknown")
        self.assertIsNone(comparison["summary"]["best_overall"])

    def test_missing_names_never_collect_wins(self):
        comparison = RepositoryComparisonService.compare(
            [
                {"analysis": {"activity_score": 90}},
                {"analysis": {"activity_score": 10}},
            ]
        )

        self.assertEqual(comparison["summary"]["wins"], {None: 0})

    def test_the_results_are_not_modified(self):
        results = [
            result("a/one", {"activity": 90}),
            result("b/two", {"activity": 60}),
        ]
        before = copy.deepcopy(results)

        RepositoryComparisonService.compare(results)

        self.assertEqual(results, before)


class AnalyzeAndCompareTests(SimpleTestCase):

    URLS = [
        "https://github.com/a/one",
        "https://github.com/b/two",
    ]

    def test_every_repository_is_analyzed_in_order_for_the_user(self):
        user = object()
        responses = {
            self.URLS[0]: result("a/one", {"overall": 90}),
            self.URLS[1]: result("b/two", {"overall": 50}),
        }

        with patch(
            ANALYZE,
            side_effect=lambda url, user=None, **kwargs: responses[url],
        ) as mock_analyze:
            comparison = RepositoryComparisonService.analyze_and_compare(
                self.URLS,
                user=user,
            )

        self.assertEqual(
            [call.args[0] for call in mock_analyze.call_args_list],
            self.URLS,
        )
        for call in mock_analyze.call_args_list:
            self.assertIs(call.kwargs["user"], user)

        self.assertEqual(comparison["summary"]["best_overall"], "a/one")

    def test_the_number_of_repositories_is_checked(self):
        invalid = [
            [],
            ["https://github.com/a/one"],
            [f"https://github.com/a/r{i}" for i in range(5)],
            None,
            "https://github.com/a/one",
        ]

        for urls in invalid:
            with self.subTest(urls=urls):
                with patch(ANALYZE) as mock_analyze:
                    with self.assertRaises(ValueError):
                        RepositoryComparisonService.analyze_and_compare(urls)

                mock_analyze.assert_not_called()

    def test_not_found_says_which_repository_failed(self):
        def analyze(url, user=None, **kwargs):
            if url == self.URLS[1]:
                raise GitHubNotFoundError("missing")

            return result("a/one")

        with patch(ANALYZE, side_effect=analyze):
            with self.assertRaises(GitHubNotFoundError) as context:
                RepositoryComparisonService.analyze_and_compare(self.URLS)

        self.assertEqual(context.exception.repository_url, self.URLS[1])

    def test_a_failure_stops_the_comparison(self):
        urls = self.URLS + ["https://github.com/c/three"]

        with patch(
            ANALYZE,
            side_effect=[result("a/one"), GitHubRateLimitError("limit")],
        ) as mock_analyze:
            with self.assertRaises(GitHubRateLimitError):
                RepositoryComparisonService.analyze_and_compare(urls)

        self.assertEqual(mock_analyze.call_count, 2)
