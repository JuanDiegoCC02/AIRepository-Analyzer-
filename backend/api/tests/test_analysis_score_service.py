from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.analysis_score_service import AnalysisScoreService


class AnalysisScoreServiceTests(SimpleTestCase):

    def test_normalize_score_returns_zero_for_none(self):
        self.assertEqual(
            AnalysisScoreService.normalize_score(None),
            0,
        )

    def test_normalize_score_returns_zero_for_invalid_value(self):
        self.assertEqual(
            AnalysisScoreService.normalize_score("invalid"),
            0,
        )

    def test_normalize_score_limits_values_to_valid_range(self):
        self.assertEqual(
            AnalysisScoreService.normalize_score(-10),
            0,
        )
        self.assertEqual(
            AnalysisScoreService.normalize_score(120),
            100,
        )

    def test_normalize_score_rounds_decimals_to_integers(self):
        for value, expected in ((85.4, 85), (85.6, 86), (89.0, 89)):
            with self.subTest(value=value):
                result = AnalysisScoreService.normalize_score(value)

                self.assertEqual(result, expected)
                self.assertIsInstance(result, int)

    def test_normalize_score_rejects_values_that_are_not_finite(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assertEqual(
                    AnalysisScoreService.normalize_score(value),
                    0,
                )

    def test_get_score_level_uses_expected_thresholds(self):
        cases = [
            (90, "Excellent"),
            (75, "Good"),
            (50, "Average"),
            (49, "Needs Improvement"),
        ]

        for score, expected_level in cases:
            with self.subTest(score=score):
                self.assertEqual(
                    AnalysisScoreService.get_score_level(score),
                    expected_level,
                )

    @patch(
        "api.services.analysis_score_service.OverallScoreService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.CommunityService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.CodeQualityService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.MaintainabilityService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.DocumentationService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.ActivityService.calculate"
    )
    @patch(
        "api.services.analysis_score_service.RepositoryScore.popularity"
    )
    def test_calculate_scores_normalizes_results(
        self,
        mock_popularity,
        mock_activity,
        mock_documentation,
        mock_maintainability,
        mock_code_quality,
        mock_community,
        mock_overall,
    ):
        mock_popularity.return_value = 120
        mock_activity.return_value = -10
        mock_documentation.return_value = 70
        mock_maintainability.return_value = 80
        mock_code_quality.return_value = 90
        mock_community.return_value = 60
        mock_overall.return_value = 75

        repository = SimpleNamespace(stars=1000)
        github_repository = {"name": "example"}

        result = AnalysisScoreService.calculate_scores(
            repository,
            github_repository,
        )

        self.assertEqual(result["popularity_score"], 100)
        self.assertEqual(result["activity_score"], 0)
        self.assertEqual(result["documentation_score"], 70)
        self.assertEqual(result["maintainability_score"], 80)
        self.assertEqual(result["code_quality_score"], 90)
        self.assertEqual(result["community_score"], 60)
        self.assertEqual(result["overall_score"], 75)
        self.assertEqual(result["level"], "Good")

        mock_overall.assert_called_once_with(
            100,
            0,
            70,
            80,
            90,
            60,
        )

    @patch(
        "api.services.analysis_score_service.MaintainabilityService.calculate"
    )
    def test_calculate_scores_gives_contributors_to_maintainability(
        self,
        mock_maintainability,
    ):
        mock_maintainability.return_value = 80
        contributors = {"contributors": [{"login": "a", "contributions": 1}]}
        github_repository = {}

        result = AnalysisScoreService.calculate_scores(
            SimpleNamespace(stars=1000),
            github_repository,
            contributors=contributors,
        )

        mock_maintainability.assert_called_once_with(
            github_repository,
            contributors=contributors,
        )

        for name, value in result.items():
            if name.endswith("_score"):
                with self.subTest(score=name):
                    self.assertIsInstance(value, int)
