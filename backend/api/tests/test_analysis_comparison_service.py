from types import SimpleNamespace

from django.test import SimpleTestCase

from api.services.analysis_comparison_service import (AnalysisComparisonService,)


class AnalysisComparisonServiceTests(SimpleTestCase):
    """Tests for repository analysis comparisons."""

    def test_calculate_positive_difference(self):
        difference = AnalysisComparisonService.calculate_difference(
            80, 65
        )

        self.assertEqual(difference, 15)

    def test_calculate_negative_difference(self):
        difference = AnalysisComparisonService.calculate_difference(
            60, 75
        )

        self.assertEqual(difference, -15)

    def test_calculate_difference_when_score_is_missing(self):
        self.assertIsNone(
            AnalysisComparisonService.calculate_difference(None, 75)
        )
        self.assertIsNone(
            AnalysisComparisonService.calculate_difference(75, None)
        )

    def test_determine_trend(self):
        self.assertEqual(
            AnalysisComparisonService.determine_trend(5),
            "Improving",
        )
        self.assertEqual(
            AnalysisComparisonService.determine_trend(-5),
            "Declining",
        )
        self.assertEqual(
            AnalysisComparisonService.determine_trend(1),
            "Stable",
        )
        self.assertEqual(
            AnalysisComparisonService.determine_trend(-1),
            "Stable",
        )
        self.assertEqual(
            AnalysisComparisonService.determine_trend(0),
            "Stable",
        )
        self.assertEqual(
            AnalysisComparisonService.determine_trend(None),
            "Unavailable",
        )

    def test_compare_score_returns_expected_structure(self):
        result = AnalysisComparisonService.compare_score(80, 65)

        self.assertEqual(
            result,
            {
                "current": 80,
                "previous": 65,
                "difference": 15,
                "trend": "Improving",
            },
        )

    def test_compare_returns_empty_dictionary_if_analysis_is_missing(self):
        self.assertEqual(
            AnalysisComparisonService.compare(None, None),
            {},
        )
        self.assertEqual(
            AnalysisComparisonService.compare(
                SimpleNamespace(overall_score=80),
                None,
            ),
            {},
        )

    def test_compare_all_seven_score_dimensions(self):
        current = SimpleNamespace(
            popularity_score=80,
            activity_score=70,
            documentation_score=90,
            maintainability_score=75,
            code_quality_score=85,
            community_score=60,
            overall_score=78,
        )

        previous = SimpleNamespace(
            popularity_score=70,
            activity_score=75,
            documentation_score=80,
            maintainability_score=75,
            code_quality_score=80,
            community_score=65,
            overall_score=70,
        )

        result = AnalysisComparisonService.compare(current, previous)

        self.assertEqual(
            set(result.keys()),
            set(AnalysisComparisonService.SCORE_FIELDS.keys()),
        )

        self.assertEqual(result["popularity"]["difference"], 10)
        self.assertEqual(result["popularity"]["trend"], "Improving")

        self.assertEqual(result["activity"]["difference"], -5)
        self.assertEqual(result["activity"]["trend"], "Declining")

        self.assertEqual(result["maintainability"]["difference"], 0)
        self.assertEqual(result["maintainability"]["trend"], "Stable")

        self.assertEqual(result["overall"]["current"], 78)
        self.assertEqual(result["overall"]["previous"], 70)
        self.assertEqual(result["overall"]["difference"], 8)
        self.assertEqual(result["overall"]["trend"], "Improving")

    def test_compare_score_with_missing_values(self):
        result = AnalysisComparisonService.compare_score(None, 70)

        self.assertIsNone(result["difference"])
        self.assertEqual(result["trend"], "Unavailable")
