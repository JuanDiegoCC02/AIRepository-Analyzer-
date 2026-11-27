from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase

from api.exceptions.github_exceptions import GitHubRateLimitError
from api.models.analysis import Analysis
from api.models.repository import Repository
from api.services.analyzer_service import AnalyzerService
from api.services.resources_cache_service import ResourcesCacheService

SERVICE = "api.services.analyzer_service"

REPOSITORY_URL = "https://github.com/facebook/react"

GITHUB_REPOSITORY = {
    "id": 123456789,
    "name": "react",
    "owner": {"login": "facebook"},
    "description": "A JavaScript library for building user interfaces.",
    "html_url": "https://github.com/facebook/react",
    "topics": ["javascript", "react"],
    "language": "JavaScript",
    "license": {"name": "MIT License"},
    "default_branch": "main",
    "stargazers_count": 100,
    "forks_count": 20,
    "watchers_count": 100,
    "subscribers_count": 40,
    "open_issues_count": 10,
    "created_at": "2020-01-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
    "pushed_at": "2026-10-01T00:00:00Z",
}

SCORES = {
    "popularity_score": 80,
    "activity_score": 75,
    "documentation_score": 70,
    "maintainability_score": 85,
    "code_quality_score": 75,
    "community_score": 80,
    "overall_score": 78,
}

# GitHub could not provide commits and structure.
INCOMPLETE = {
    "CommitsService.analyze": {"available": False},
    "RepositoryStructureService.analyze": {
        "available": False,
        "entries": {},
        "workflows": None,
    },
}

# Everything was retrieved: the result can be cached.
COMPLETE = {
    "CommitsService.analyze": {"available": True, "commits": 5},
    "RepositoryStructureService.analyze": {
        "available": True,
        "entries": {},
        "workflows": [],
    },
}


def patch_pipeline(resources=None):
    """
    Patch everything that would call GitHub or other slow services.

    Returns an ExitStack (use it with `with`). The mocks are available as
    `stack.mocks[name]`. Every patch is applied where AnalyzerService
    imports it.
    """
    values = {
        "GitHubService.get_repository": GITHUB_REPOSITORY,
        "AnalysisScoreService.calculate_scores": SCORES,
        "AnalysisEvaluationService.generate": {"status": "good"},
        "RecommendationService.generate": ["Improve test coverage"],
        "AIInsightsService.generate": None,
        "AISummaryService.generate": "A React repository summary.",
        "RepositoryInsightsService.generate": {"strengths": []},
        "TechnologiesService.analyze": {"languages": ["JavaScript"]},
        "ReadmeService.load_analysis": {"available": True, "exists": True},
        "ContributorsService.get_contributors": [],
        "ContributorsService.summarize": {"total": 0},
        "RepositoryStatisticsService.generate": {"stars": 100},
        "RepositoryTopicsService.analyze": {"topics": ["javascript"]},
        "ReleaseAnalysisService.analyze": {"total": 0},
        "RepositoryHealthService.generate": {"status": "good"},
    }
    values.update(INCOMPLETE if resources is None else resources)

    stack = ExitStack()
    stack.mocks = {}

    for target, return_value in values.items():
        stack.mocks[target] = stack.enter_context(
            patch(f"{SERVICE}.{target}", return_value=return_value)
        )

    return stack


class AnalyzerServiceTests(TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_analyze_repository_returns_expected_structure(self):
        with patch_pipeline() as pipeline:
            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        for key in (
            "repository",
            "analysis",
            "analysis_result",
            "technologies",
            "topics",
            "statistics",
            "classification",
            "insights",
            "contributors",
            "readme",
            "health",
            "maturity",
            "releases",
            "commits",
            "code_quality_signals",
            "maintainability_signals",
            "data_quality",
            "evaluation",
            "recommendations",
        ):
            with self.subTest(key=key):
                self.assertIn(key, response)

        self.assertEqual(response["commits"], {"available": False})
        self.assertEqual(
            response["analysis"]["score_version"],
            Analysis.CURRENT_SCORE_VERSION,
        )
        self.assertEqual(
            response["analysis"]["ai_summary"],
            "A React repository summary.",
        )
        self.assertEqual(
            response["recommendations"],
            ["Improve test coverage"],
        )

        # Structure unavailable: no code quality signal has points.
        for signal in response["code_quality_signals"].values():
            self.assertIsNone(signal["points"])

        self.assertEqual(
            Repository.objects.filter(github_id=123456789).count(),
            1,
        )
        self.assertEqual(Analysis.objects.count(), 1)

        pipeline.mocks["GitHubService.get_repository"].assert_called_once()
        pipeline.mocks[
            "AnalysisScoreService.calculate_scores"
        ].assert_called_once()
        pipeline.mocks["AISummaryService.generate"].assert_called_once()

    def test_data_quality_lists_the_resources_that_are_missing(self):
        with patch_pipeline():
            incomplete = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            incomplete["data_quality"],
            {"complete": False, "missing": ["commits", "structure"]},
        )

        cache.clear()

        with patch_pipeline(COMPLETE):
            complete = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            complete["data_quality"],
            {"complete": True, "missing": []},
        )

    def test_watchers_are_the_real_subscribers_not_the_stars(self):
        with patch_pipeline():
            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(response["repository"]["stars"], 100)
        self.assertEqual(response["repository"]["watchers"], 40)

    def test_missing_subscribers_are_saved_as_zero(self):
        without = dict(GITHUB_REPOSITORY)
        without.pop("subscribers_count")

        with patch_pipeline() as pipeline:
            pipeline.mocks[
                "GitHubService.get_repository"
            ].return_value = without

            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(response["repository"]["watchers"], 0)

    def test_analysis_is_kept_when_summary_fails(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks[
                "AISummaryService.generate"
            ].side_effect = RuntimeError("Summary generation failed")

            with self.assertLogs(
                "api.services.analyzer_service",
                level="ERROR",
            ):
                response = AnalyzerService.analyze_repository(
                    REPOSITORY_URL
                )

        self.assertEqual(Analysis.objects.count(), 1)
        self.assertFalse(response["analysis"]["ai_summary"])
        self.assertEqual(
            response["recommendations"],
            ["Improve test coverage"],
        )

    def test_empty_summary_is_not_saved_over_the_analysis(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks["AISummaryService.generate"].return_value = None

            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertFalse(response["analysis"]["ai_summary"])
        self.assertEqual(Analysis.objects.count(), 1)

    def test_analysis_is_rolled_back_when_insights_fail(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks[
                "RepositoryInsightsService.generate"
            ].side_effect = RuntimeError("Insights generation failed")

            with self.assertRaisesMessage(
                RuntimeError,
                "Insights generation failed",
            ):
                AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(Analysis.objects.count(), 0)

        # The repository may stay saved: it is created before the
        # analysis transaction starts.
        self.assertEqual(
            Repository.objects.filter(github_id=123456789).count(),
            1,
        )

        pipeline.mocks["RepositoryInsightsService.generate"].assert_called_once()

    def test_analysis_is_rolled_back_when_recommendations_fail(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks[
                "RecommendationService.generate"
            ].side_effect = RuntimeError("Recommendations failed")

            with self.assertRaises(RuntimeError):
                AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(Analysis.objects.count(), 0)
        pipeline.mocks["AISummaryService.generate"].assert_not_called()


class AnalyzerServiceCacheTests(TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_second_analysis_reuses_the_github_data(self):
        with patch_pipeline(COMPLETE) as pipeline:
            AnalyzerService.analyze_repository(REPOSITORY_URL)
            AnalyzerService.analyze_repository(REPOSITORY_URL)

        mocks = pipeline.mocks

        # The repository itself is always requested again...
        self.assertEqual(
            mocks["GitHubService.get_repository"].call_count,
            2,
        )

        # ...but the other requests are made only once.
        for name in (
            "TechnologiesService.analyze",
            "ReadmeService.load_analysis",
            "ContributorsService.get_contributors",
            "ReleaseAnalysisService.analyze",
            "CommitsService.analyze",
            "RepositoryStructureService.analyze",
        ):
            with self.subTest(name=name):
                self.assertEqual(mocks[name].call_count, 1)

        # Every analysis is still saved and scored.
        self.assertEqual(Analysis.objects.count(), 2)
        self.assertEqual(
            mocks["AnalysisScoreService.calculate_scores"].call_count,
            2,
        )

    def test_incomplete_data_is_not_cached(self):
        with patch_pipeline(INCOMPLETE) as pipeline:
            AnalyzerService.analyze_repository(REPOSITORY_URL)
            AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            pipeline.mocks["CommitsService.analyze"].call_count,
            2,
        )

    def test_a_new_push_makes_the_data_be_collected_again(self):
        with patch_pipeline(COMPLETE) as pipeline:
            AnalyzerService.analyze_repository(REPOSITORY_URL)

            pipeline.mocks["GitHubService.get_repository"].return_value = (
                dict(GITHUB_REPOSITORY, pushed_at="2026-11-01T00:00:00Z")
            )

            AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            pipeline.mocks["CommitsService.analyze"].call_count,
            2,
        )

    def test_cache_can_be_disabled(self):
        with patch.object(ResourcesCacheService, "ttl", return_value=0):
            with patch_pipeline(COMPLETE) as pipeline:
                AnalyzerService.analyze_repository(REPOSITORY_URL)
                AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            pipeline.mocks["CommitsService.analyze"].call_count,
            2,
        )

    def test_a_broken_cache_does_not_break_the_analysis(self):
        broken_cache = MagicMock()
        broken_cache.get.side_effect = RuntimeError("cache down")
        broken_cache.set.side_effect = RuntimeError("cache down")

        with patch(
            "api.services.resources_cache_service.cache",
            broken_cache,
        ):
            with patch_pipeline(COMPLETE):
                with self.assertLogs(
                    "api.services.resources_cache_service",
                    level="WARNING",
                ):
                    response = AnalyzerService.analyze_repository(
                        REPOSITORY_URL
                    )

        self.assertIn("analysis", response)
        self.assertEqual(Analysis.objects.count(), 1)

    def test_rate_limit_stops_the_analysis_and_saves_nothing(self):
        with patch_pipeline(COMPLETE) as pipeline:
            pipeline.mocks[
                "CommitsService.analyze"
            ].side_effect = GitHubRateLimitError("limit", retry_after=30)

            with self.assertRaises(GitHubRateLimitError) as context:
                AnalyzerService.analyze_repository(REPOSITORY_URL)

            self.assertEqual(context.exception.retry_after, 30)
            self.assertEqual(Analysis.objects.count(), 0)

            scores_mock = pipeline.mocks[
                "AnalysisScoreService.calculate_scores"
            ]
            scores_mock.assert_not_called()

            # Nothing was cached: the next try collects the data again.
            pipeline.mocks["CommitsService.analyze"].side_effect = None

            AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(
            pipeline.mocks["CommitsService.analyze"].call_count,
            2,
        )
        self.assertEqual(Analysis.objects.count(), 1)


class AnalyzerServiceTransactionTests(TransactionTestCase):
    """
    TestCase wraps every test in a transaction, which would hide whether
    the summary runs inside the analysis transaction. This class does not.
    """

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_summary_is_generated_outside_the_transaction(self):
        observed = []

        def generate(*args, **kwargs):
            observed.append(connection.in_atomic_block)
            return "A React repository summary."

        with patch_pipeline() as pipeline:
            pipeline.mocks["AISummaryService.generate"].side_effect = generate

            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(observed, [False])
        self.assertEqual(
            response["analysis"]["ai_summary"],
            "A React repository summary.",
        )
        self.assertEqual(
            Analysis.objects.get().ai_summary,
            "A React repository summary.",
        )


class AnalyzerServiceAISummaryTests(TestCase):
    """The AI summary is tried first; the template is the fallback."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_ai_summary_is_saved_and_marked_as_ai(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks["AIInsightsService.generate"].return_value = (
                "A summary written by the AI model."
            )

            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(response["summary_source"], "ai")
        self.assertEqual(
            response["analysis"]["ai_summary"],
            "A summary written by the AI model.",
        )
        self.assertEqual(
            Analysis.objects.get().ai_summary,
            "A summary written by the AI model.",
        )
        pipeline.mocks["AISummaryService.generate"].assert_not_called()

    def test_template_is_used_when_the_ai_gives_nothing(self):
        with patch_pipeline() as pipeline:
            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(response["summary_source"], "template")
        self.assertEqual(
            response["analysis"]["ai_summary"],
            "A React repository summary.",
        )
        pipeline.mocks["AIInsightsService.generate"].assert_called_once()

    def test_template_is_used_when_the_ai_raises(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks[
                "AIInsightsService.generate"
            ].side_effect = RuntimeError("AI exploded")

            with self.assertLogs(
                "api.services.analyzer_service",
                level="ERROR",
            ):
                response = AnalyzerService.analyze_repository(
                    REPOSITORY_URL
                )

        self.assertEqual(response["summary_source"], "template")
        self.assertEqual(Analysis.objects.count(), 1)

    def test_use_ai_false_never_calls_the_ai(self):
        with patch_pipeline() as pipeline:
            response = AnalyzerService.analyze_repository(
                REPOSITORY_URL,
                use_ai=False,
            )

        pipeline.mocks["AIInsightsService.generate"].assert_not_called()
        self.assertEqual(response["summary_source"], "template")

    def test_source_is_none_when_there_is_no_summary(self):
        with patch_pipeline() as pipeline:
            pipeline.mocks["AISummaryService.generate"].return_value = None

            response = AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertIsNone(response["summary_source"])


class AnalyzerServiceAITransactionTests(TransactionTestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_the_ai_call_runs_outside_the_transaction(self):
        observed = []

        def generate(*args, **kwargs):
            observed.append(connection.in_atomic_block)
            return "A summary written by the AI model."

        with patch_pipeline() as pipeline:
            pipeline.mocks["AIInsightsService.generate"].side_effect = generate

            AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(observed, [False])
