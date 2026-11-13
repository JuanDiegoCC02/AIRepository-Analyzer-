from contextlib import ExitStack
from unittest.mock import patch

from django.test import TestCase

from api.models.analysis import Analysis
from api.models.repository import Repository
from api.services.analyzer_service import AnalyzerService

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
    "open_issues_count": 10,
    "created_at": "2020-01-01T00:00:00Z",
    "updated_at": "2026-10-01T00:00:00Z",
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


def patch_external_services():
    """Patch every service that would call GitHub or other resources.

    Returns an ExitStack: use it as a context manager (`with ...:`).
    Every patch is applied where AnalyzerService imports it.
    """
    stack = ExitStack()

    patches = [
        ("TechnologiesService.analyze", {"languages": ["JavaScript"]}),
        ("ReadmeService.get_readme", "# React"),
        ("ReadmeService.analyze", {"available": True}),
        ("ContributorsService.get_contributors", []),
        ("ContributorsService.summarize", {"total": 0}),
        ("RepositoryStatisticsService.generate", {"stars": 100}),
        (
            "RepositoryTopicsService.analyze",
            {"topics": ["javascript", "react"]},
        ),
        ("RepositoryMaturityService.calculate", {"level": "mature"}),
        ("ReleaseAnalysisService.analyze", {"total": 0}),
        ("CommitsService.analyze", {"available": False}),
        (
            "RepositoryStructureService.analyze",
            {"available": False, "entries": {}, "workflows": None},
        ),
        ("RepositoryHealthService.generate", {"status": "good"}),
    ]

    for target, return_value in patches:
        stack.enter_context(
            patch(f"{SERVICE}.{target}", return_value=return_value)
        )

    return stack


class AnalyzerServiceTests(TestCase):

    @patch(f"{SERVICE}.RepositoryInsightsService.generate")
    @patch(f"{SERVICE}.AISummaryService.generate")
    @patch(f"{SERVICE}.RecommendationService.generate")
    @patch(f"{SERVICE}.AnalysisEvaluationService.generate")
    @patch(f"{SERVICE}.AnalysisScoreService.calculate_scores")
    @patch(f"{SERVICE}.GitHubService.get_repository")
    def test_analyze_repository_returns_expected_structure(
        self,
        mock_get_repository,
        mock_calculate_scores,
        mock_generate_evaluation,
        mock_generate_recommendations,
        mock_generate_summary,
        mock_generate_insights,
    ):
        mock_get_repository.return_value = GITHUB_REPOSITORY
        mock_calculate_scores.return_value = SCORES
        mock_generate_evaluation.return_value = {"status": "good"}
        mock_generate_recommendations.return_value = [
            "Improve test coverage",
        ]
        mock_generate_summary.return_value = "A React repository summary."
        mock_generate_insights.return_value = {"strengths": []}

        with patch_external_services():
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

        # Structure unavailable: no code quality signal has points.
        for signal in response["code_quality_signals"].values():
            self.assertIsNone(signal["points"])

        self.assertEqual(
            Repository.objects.filter(github_id=123456789).count(),
            1,
        )
        self.assertEqual(Analysis.objects.count(), 1)

        mock_get_repository.assert_called_once()
        mock_calculate_scores.assert_called_once()
        mock_generate_summary.assert_called_once()

    @patch(f"{SERVICE}.RepositoryInsightsService.generate")
    @patch(f"{SERVICE}.AISummaryService.generate")
    @patch(f"{SERVICE}.RecommendationService.generate")
    @patch(f"{SERVICE}.AnalysisEvaluationService.generate")
    @patch(f"{SERVICE}.AnalysisScoreService.calculate_scores")
    @patch(f"{SERVICE}.GitHubService.get_repository")
    def test_analysis_is_rolled_back_when_summary_fails(
        self,
        mock_get_repository,
        mock_calculate_scores,
        mock_evaluation,
        mock_recommendations,
        mock_summary,
        mock_insights,
    ):
        mock_get_repository.return_value = GITHUB_REPOSITORY
        mock_calculate_scores.return_value = SCORES
        mock_evaluation.return_value = {"status": "good"}
        mock_recommendations.return_value = ["Improve test coverage"]
        mock_summary.side_effect = RuntimeError(
            "Summary generation failed"
        )

        with patch_external_services():
            with self.assertRaisesMessage(
                RuntimeError,
                "Summary generation failed",
            ):
                AnalyzerService.analyze_repository(REPOSITORY_URL)

        self.assertEqual(Analysis.objects.count(), 0)

    @patch(f"{SERVICE}.RepositoryInsightsService.generate")
    @patch(f"{SERVICE}.AISummaryService.generate")
    @patch(f"{SERVICE}.RecommendationService.generate")
    @patch(f"{SERVICE}.AnalysisEvaluationService.generate")
    @patch(f"{SERVICE}.AnalysisScoreService.calculate_scores")
    @patch(f"{SERVICE}.GitHubService.get_repository")
    def test_analysis_is_rolled_back_when_insights_fail(
        self,
        mock_get_repository,
        mock_calculate_scores,
        mock_evaluation,
        mock_recommendations,
        mock_summary,
        mock_insights,
    ):
        mock_get_repository.return_value = GITHUB_REPOSITORY
        mock_calculate_scores.return_value = SCORES
        mock_evaluation.return_value = {"status": "good"}
        mock_recommendations.return_value = ["Improve test coverage"]
        mock_summary.return_value = "A React repository summary."
        mock_insights.side_effect = RuntimeError(
            "Insights generation failed"
        )

        with patch_external_services():
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

        mock_insights.assert_called_once()