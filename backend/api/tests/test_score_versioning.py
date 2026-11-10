from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from api.models.analysis import Analysis
from api.models.repository import Repository
from api.serializers.analysis_serializer import AnalysisSerializer
from api.services.analysis_evaluation_service import AnalysisEvaluationService
from api.services.analysis_history_service import AnalysisHistoryService
from api.services.analysis_persistence_service import (
    AnalysisPersistenceService,
)

User = get_user_model()


class ScoreVersioningTests(TestCase):

    def setUp(self):
        now = timezone.now()

        self.repository = Repository.objects.create(
            github_id=777001,
            owner="pallets",
            name="flask",
            full_name="pallets/flask",
            html_url="https://github.com/pallets/flask",
            github_created_at=now,
            github_updated_at=now,
        )

        self.user = User.objects.create_user(
            username="versioning-user",
            password="test-password-123",
        )

    def create_analysis(self, score, score_version=None):
        values = {
            "repository": self.repository,
            "user": self.user,
            "project_type": "Backend",
            "popularity_score": score,
            "activity_score": score,
            "documentation_score": score,
            "maintainability_score": score,
            "code_quality_score": score,
            "community_score": score,
            "overall_score": score,
        }

        if score_version is not None:
            values["score_version"] = score_version

        return Analysis.objects.create(**values)

    def test_analysis_created_without_version_is_legacy(self):
        analysis = self.create_analysis(50)

        self.assertEqual(
            analysis.score_version,
            Analysis.LEGACY_SCORE_VERSION,
        )

    def test_persistence_service_stores_the_current_version(self):
        scores = {
            "popularity_score": 90,
            "activity_score": 80,
            "documentation_score": 75,
            "maintainability_score": 85,
            "code_quality_score": 70,
            "community_score": 88,
            "overall_score": 81,
        }

        analysis = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Backend",
            scores=scores,
            summary="Summary",
            recommendations=[],
            user=self.user,
        )

        self.assertEqual(
            analysis.score_version,
            Analysis.CURRENT_SCORE_VERSION,
        )

    def test_current_version_is_newer_than_legacy(self):
        self.assertGreater(
            Analysis.CURRENT_SCORE_VERSION,
            Analysis.LEGACY_SCORE_VERSION,
        )

    def test_history_previous_can_be_limited_to_one_version(self):
        current = Analysis.CURRENT_SCORE_VERSION
        legacy = Analysis.LEGACY_SCORE_VERSION

        older_current = self.create_analysis(70, current)
        self.create_analysis(40, legacy)
        self.create_analysis(80, current)

        unfiltered = AnalysisHistoryService.get_previous(
            self.repository,
            user=self.user,
        )
        filtered = AnalysisHistoryService.get_previous(
            self.repository,
            user=self.user,
            score_version=current,
        )

        self.assertEqual(unfiltered.score_version, legacy)
        self.assertEqual(filtered.id, older_current.id)

    def test_evaluation_ignores_analyses_from_older_formulas(self):
        self.create_analysis(
            95,
            Analysis.LEGACY_SCORE_VERSION,
        )

        current = self.create_analysis(
            60,
            Analysis.CURRENT_SCORE_VERSION,
        )

        result = AnalysisEvaluationService.generate(
            self.repository,
            current,
        )

        # Without this rule the evaluation would report a false
        # "Declining" trend (95 -> 60) caused only by the new formula.
        self.assertFalse(result["available"])
        self.assertIsNone(result["comparison"])

    def test_evaluation_compares_analyses_with_the_same_formulas(self):
        self.create_analysis(
            95,
            Analysis.LEGACY_SCORE_VERSION,
        )

        previous = self.create_analysis(
            60,
            Analysis.CURRENT_SCORE_VERSION,
        )

        current = self.create_analysis(
            75,
            Analysis.CURRENT_SCORE_VERSION,
        )

        result = AnalysisEvaluationService.generate(
            self.repository,
            current,
        )

        self.assertTrue(result["available"])
        self.assertEqual(result["previous_analysis_id"], previous.id)
        self.assertEqual(result["overall_trend"], "Improving")
        self.assertEqual(result["overall_difference"], 15)

    def test_serializer_exposes_the_score_version(self):
        analysis = self.create_analysis(
            50,
            Analysis.CURRENT_SCORE_VERSION,
        )

        data = AnalysisSerializer(analysis).data

        self.assertEqual(
            data["score_version"],
            Analysis.CURRENT_SCORE_VERSION,
        )