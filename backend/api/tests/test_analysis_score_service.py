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

    def test_normalize_score_preserves_valid_decimal(self):
        self.assertEqual(
            AnalysisScoreService.normalize_score(85.5),
            85.5,
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