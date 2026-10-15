from django.test import SimpleTestCase

from api.services.analysis_result_service import AnalysisResultService


class AnalysisResultServiceTests(SimpleTestCase):

    def test_build_returns_overall_and_all_dimensions(self):
        scores = {
            "overall_score": 80,
            "level": "Good",
            "popularity_score": 100,
            "activity_score": 85,
            "documentation_score": 70,
            "maintainability_score": 90,
            "code_quality_score": 50,
            "community_score": 85,
        }

        result = AnalysisResultService.build(scores)

        self.assertEqual(
            result["overall"],
            {
                "score": 80,
                "level": "Good",
            },
        )

        self.assertEqual(
            result["dimensions"],
            {
                "popularity": 100,
                "activity": 85,
                "documentation": 70,
                "maintainability": 90,
                "code_quality": 50,
                "community": 85,
            },
        )

    def test_build_uses_level_from_input_when_available(self):
        result = AnalysisResultService.build({
            "overall_score": 92,
            "level": "Custom Level",
        })

        self.assertEqual(
            result["overall"]["level"],
            "Custom Level",
        )

    def test_build_derives_level_when_missing(self):
        result = AnalysisResultService.build({
            "overall_score": 75,
        })

        self.assertEqual(
            result["overall"]["level"],
            "Good",
        )

    def test_build_defaults_missing_scores_to_zero(self):
        result = AnalysisResultService.build({})

        self.assertEqual(
            result["overall"],
            {
                "score": 0,
                "level": "Needs Improvement",
            },
        )

        self.assertEqual(
            result["dimensions"],
            {
                "popularity": 0,
                "activity": 0,
                "documentation": 0,
                "maintainability": 0,
                "code_quality": 0,
                "community": 0,
            },
        )