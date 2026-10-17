from django.test import TestCase
from django.utils import timezone

from api.models.analysis import Analysis
from api.models.repository import Repository
from api.services.analysis_persistence_service import (AnalysisPersistenceService,)


class AnalysisPersistenceServiceTests(TestCase):

    def setUp(self):
        now = timezone.now()

        self.repository = Repository.objects.create(
            github_id=123456789,
            owner="test-owner",
            name="test-repository",
            full_name="test-owner/test-repository",
            description="Repository for persistence tests",
            html_url="https://github.com/test-owner/test-repository",
            github_created_at=now,
            github_updated_at=now,
        )

        self.scores = {
            "popularity_score": 90,
            "activity_score": 80,
            "documentation_score": 75,
            "maintainability_score": 85,
            "code_quality_score": 70,
            "community_score": 80,
            "overall_score": 80,
        }

    def test_save_analysis_persists_all_fields(self):
        analysis = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=self.scores,
            summary="Analysis summary",
            recommendations=[
                "Improve documentation",
                "Add automated tests",
            ],
        )

        analysis.refresh_from_db()

        self.assertEqual(analysis.repository, self.repository)
        self.assertEqual(analysis.project_type, "Web Application")
        self.assertEqual(analysis.popularity_score, 90)
        self.assertEqual(analysis.activity_score, 80)
        self.assertEqual(analysis.documentation_score, 75)
        self.assertEqual(analysis.maintainability_score, 85)
        self.assertEqual(analysis.code_quality_score, 70)
        self.assertEqual(analysis.community_score, 80)
        self.assertEqual(analysis.overall_score, 80)
        self.assertEqual(analysis.ai_summary, "Analysis summary")
        self.assertEqual(
            analysis.recommendations,
            "Improve documentation\nAdd automated tests",
        )

    def test_save_analysis_creates_a_new_history_record(self):
        first = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=self.scores,
            summary="First analysis",
            recommendations=[],
        )

        second = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=self.scores,
            summary="Second analysis",
            recommendations=[],
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(
            Analysis.objects.filter(
                repository=self.repository
            ).count(),
            2,
        )

    def test_save_analysis_handles_empty_recommendations(self):
        analysis = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=self.scores,
            summary="",
            recommendations=[],
        )

        self.assertEqual(analysis.recommendations, "")
        self.assertEqual(analysis.ai_summary, "")


        
    def test_save_analysis_rejects_missing_score(self):
        scores = self.scores.copy()
        del scores["activity_score"]

        with self.assertRaisesMessage(
            ValueError,
            "Missing required score: activity_score.",
        ):
            AnalysisPersistenceService.save_analysis(
                repository=self.repository,
                category="Web Application",
                scores=scores,
                summary="Test",
                recommendations=[],
            )

        self.assertEqual(Analysis.objects.count(), 0)

    def test_save_analysis_rejects_score_outside_range(self):
        scores = self.scores.copy()
        scores["popularity_score"] = 101

        with self.assertRaisesMessage(
            ValueError,
            "popularity_score must be between 0 and 100.",
        ):
            AnalysisPersistenceService.save_analysis(
                repository=self.repository,
                category="Web Application",
                scores=scores,
                summary="Test",
                recommendations=[],
            )

        self.assertEqual(Analysis.objects.count(), 0)

    def test_save_analysis_rejects_fractional_score(self):
        scores = self.scores.copy()
        scores["activity_score"] = 85.5

        with self.assertRaisesMessage(
            ValueError,
            "activity_score must be a whole number.",
        ):
            AnalysisPersistenceService.save_analysis(
                repository=self.repository,
                category="Web Application",
                scores=scores,
                summary="Test",
                recommendations=[],
            )

        self.assertEqual(Analysis.objects.count(), 0)

    def test_save_analysis_accepts_integer_valued_float(self):
        scores = self.scores.copy()
        scores["activity_score"] = 80.0

        analysis = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=scores,
            summary="Test",
            recommendations=[],
        )

        self.assertEqual(analysis.activity_score, 80)

    def test_save_analysis_handles_none_recommendations(self):
        analysis = AnalysisPersistenceService.save_analysis(
            repository=self.repository,
            category="Web Application",
            scores=self.scores,
            summary="Test",
            recommendations=None,
        )

        self.assertEqual(analysis.recommendations, "")

    def test_save_analysis_rejects_non_string_recommendation(self):
        with self.assertRaisesMessage(
            ValueError,
            "Every recommendation must be a string.",
        ):
            AnalysisPersistenceService.save_analysis(
                repository=self.repository,
                category="Web Application",
                scores=self.scores,
                summary="Test",
                recommendations=["Improve tests", 123],
            )

        self.assertEqual(Analysis.objects.count(), 0)


