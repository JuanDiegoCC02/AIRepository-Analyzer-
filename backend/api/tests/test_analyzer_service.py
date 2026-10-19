from unittest.mock import patch

from django.test import TestCase

from api.models.analysis import Analysis
from api.models.repository import Repository
from api.services.analyzer_service import AnalyzerService


class AnalyzerServiceTests(TestCase):

    @patch("api.services.analyzer_service.RepositoryInsightsService.generate")
    @patch("api.services.analyzer_service.AISummaryService.generate")
    @patch("api.services.analyzer_service.RecommendationService.generate")
    @patch("api.services.analyzer_service.AnalysisEvaluationService.generate")
    @patch("api.services.analyzer_service.AnalysisScoreService.calculate_scores")
    @patch("api.services.analyzer_service.GitHubService.get_repository")

    def test_analyze_repository_returns_expected_structure(
        self,
        mock_get_repository,
        mock_calculate_scores,
        mock_generate_evaluation,
        mock_generate_recommendations,
        mock_generate_summary,
        mock_generate_insights,
    ):
        github_repository = {
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

        scores = {
            "popularity_score": 80,
            "activity_score": 75,
            "documentation_score": 70,
            "maintainability_score": 85,
            "code_quality_score": 75,
            "community_score": 80,
            "overall_score": 78,
        }

        mock_get_repository.return_value = github_repository
        mock_calculate_scores.return_value = scores
        mock_generate_evaluation.return_value = {"status": "good"}
        mock_generate_recommendations.return_value = ["Improve test coverage",]
        mock_generate_summary.return_value = "A React repository summary."
        mock_generate_insights.return_value = {"strengths": []}

        with (
            patch(
                "api.services.analyzer_service.TechnologiesService.analyze",
                return_value={"languages": ["JavaScript"]},
            ),
            patch(
                "api.services.analyzer_service.ReadmeService.get_readme",
                return_value="# React",
            ),
            patch(
                "api.services.analyzer_service.ReadmeService.analyze",
                return_value={"available": True},
            ),
            patch(
                "api.services.analyzer_service.ContributorsService.get_contributors",
                return_value=[],
            ),
            patch(
                "api.services.analyzer_service.ContributorsService.summarize",
                return_value={"total": 0},
            ),
            patch(
                "api.services.analyzer_service.RepositoryStatisticsService.generate",
                return_value={"stars": 100},
            ),
            patch(
                "api.services.analyzer_service.RepositoryTopicsService.analyze",
                return_value={"topics": ["javascript", "react"]},
            ),
            patch(
                "api.services.analyzer_service.RepositoryMaturityService.calculate",
                return_value={"level": "mature"},
            ),
            patch(
                "api.services.analyzer_service.ReleaseAnalysisService.analyze",
                return_value={"total": 0},
            ),
            patch(
                "api.services.analyzer_service.RepositoryHealthService.generate",
                return_value={"status": "good"},
            ),
        ):
            response = AnalyzerService.analyze_repository(
                "https://github.com/facebook/react"
            )

        self.assertIn("repository", response)
        self.assertIn("analysis", response)
        self.assertIn("analysis_result", response)
        self.assertIn("technologies", response)
        self.assertIn("topics", response)
        self.assertIn("statistics", response)
        self.assertIn("classification", response)
        self.assertIn("insights", response)
        self.assertIn("contributors", response)
        self.assertIn("readme", response)
        self.assertIn("health", response)
        self.assertIn("maturity", response)
        self.assertIn("releases", response)
        self.assertIn("evaluation", response)
        self.assertIn("recommendations", response)

        self.assertEqual(
            Repository.objects.filter(
                github_id=123456789
            ).count(),
            1,
        )
        self.assertEqual(Analysis.objects.count(), 1)

        mock_get_repository.assert_called_once()
        mock_calculate_scores.assert_called_once()
        mock_generate_summary.assert_called_once()
