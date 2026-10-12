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
            "activity_score": 60,
            "community_score": 30,
            "code_quality_score": 70,
        }

        result = RepositoryHealthService.generate(scores)

        self.assertEqual(result["status"], "Poor")
        self.assertEqual(result["strengths"], [])
        self.assertEqual(len(result["weaknesses"]), 4)

    def test_individual_score_threshold_is_80(self):
        scores = {
            "overall_score": 80,
            "documentation_score": 80,
            "activity_score": 79,
            "community_score": 80,
            "code_quality_score": 79,
        }

        result = RepositoryHealthService.generate(scores)

        self.assertEqual(
            result["strengths"],
            [
                "Excellent project documentation.",
                "Strong community engagement.",
            ],
        )
        self.assertEqual(
            result["weaknesses"],
            [
                "Development activity is low.",
                "Code quality can be improved.",
            ],
        )

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
