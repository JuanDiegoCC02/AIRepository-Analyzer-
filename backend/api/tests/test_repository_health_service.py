from django.test import SimpleTestCase

from api.services.repository_health_service import RepositoryHealthService


class RepositoryHealthServiceTests(SimpleTestCase):

    def test_status_thresholds(self):
        cases = [
            (90, "Excellent"),
            (75, "Good"),
            (60, "Fair"),
            (59, "Poor"),
        ]

        for score, expected_status in cases:
            with self.subTest(score=score):
                result = RepositoryHealthService.generate({
                    "overall_score": score,
                })

                self.assertEqual(result["status"], expected_status)

    def test_high_scores_generate_strengths(self):
        scores = {
            "overall_score": 95,
            "documentation_score": 90,
            "activity_score": 85,
            "community_score": 90,
            "code_quality_score": 95,
        }

        result = RepositoryHealthService.generate(scores)

        self.assertEqual(result["status"], "Excellent")
        self.assertEqual(result["overall_score"], 95)
        self.assertEqual(len(result["strengths"]), 4)
        self.assertEqual(result["weaknesses"], [])

    def test_low_scores_generate_weaknesses(self):
        scores = {
            "overall_score": 40,
            "documentation_score": 50,
            "activity_score": 20,
            "community_score": 30,
            "code_quality_score": 10,
        }

        result = RepositoryHealthService.generate(scores)

        self.assertEqual(result["status"], "Poor")
        self.assertEqual(result["strengths"], [])
        self.assertEqual(len(result["weaknesses"]), 4)

    def test_individual_score_bands(self):
        # >= 80 strength, 60-79 neutral, < 60 weakness.
        scores = {
            "overall_score": 80,
            "documentation_score": 80,
            "activity_score": 79,
            "community_score": 59,
            "code_quality_score": 60,
        }

        result = RepositoryHealthService.generate(scores)

        self.assertEqual(
            result["strengths"],
            ["Excellent project documentation."],
        )
        self.assertEqual(
            result["weaknesses"],
            ["Community engagement is limited."],
        )

    def test_neutral_scores_are_neither_strength_nor_weakness(self):
        # Flask-like activity of 71 must not be called "low".
        result = RepositoryHealthService.generate({
            "overall_score": 85,
            "documentation_score": 70,
            "activity_score": 71,
            "community_score": 65,
            "code_quality_score": 79,
        })

        self.assertEqual(result["strengths"], [])
        self.assertEqual(result["weaknesses"], [])

    def test_invalid_scores_count_as_zero(self):
        result = RepositoryHealthService.generate({
            "overall_score": "x",
            "documentation_score": True,
            "activity_score": None,
            "community_score": float("nan"),
            "code_quality_score": [],
        })

        self.assertEqual(result["status"], "Poor")
        self.assertEqual(result["overall_score"], 0)
        self.assertEqual(len(result["weaknesses"]), 4)

    def test_missing_scores_use_default_values(self):
        result = RepositoryHealthService.generate({})

        self.assertEqual(result["status"], "Poor")
        self.assertEqual(result["overall_score"], 0)
        self.assertEqual(result["strengths"], [])
        self.assertEqual(len(result["weaknesses"]), 4)

    def test_none_scores_are_handled(self):
        result = RepositoryHealthService.generate(None)

        self.assertEqual(result["status"], "Poor")
        self.assertEqual(result["overall_score"], 0)
        self.assertEqual(result["strengths"], [])
        self.assertEqual(len(result["weaknesses"]), 4)