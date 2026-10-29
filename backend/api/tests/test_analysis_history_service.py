
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from api.models.repository import Repository
from api.models.analysis import Analysis
from api.services.analysis_history_service import AnalysisHistoryService


class AnalysisHistoryServiceTests(TestCase):
    """Tests for repository analysis history queries."""

    def setUp(self):
        self.now = timezone.now()

        self.repository = Repository.objects.create(
            github_id=10001,
            owner="test-owner",
            name="test-repository",
            full_name="test-owner/test-repository",
            description="Repository used for history tests",
            topics=["python", "django"],
            html_url="https://github.com/test-owner/test-repository",
            language="Python",
            license_name="MIT License",
            default_branch="main",
            stars=100,
            forks=10,
            watchers=100,
            open_issues=5,
            github_created_at=self.now - timedelta(days=365),
            github_updated_at=self.now,
        )

    def create_analysis(self, overall_score, created_at=None):
        analysis = Analysis.objects.create(
            repository=self.repository,
            project_type="Backend",
            popularity_score=overall_score,
            activity_score=overall_score,
            documentation_score=overall_score,
            maintainability_score=overall_score,
            code_quality_score=overall_score,
            community_score=overall_score,
            overall_score=overall_score,
        )

        if created_at is not None:
            Analysis.objects.filter(pk=analysis.pk).update(
                created_at=created_at
            )
            analysis.refresh_from_db()

        return analysis

    def test_get_history_returns_newest_first(self):
        oldest = self.create_analysis(
            40,
            self.now - timedelta(days=3),
        )
        newest = self.create_analysis(
            90,
            self.now - timedelta(days=1),
        )
        middle = self.create_analysis(
            60,
            self.now - timedelta(days=2),
        )

        history = list(
            AnalysisHistoryService.get_history(self.repository)
        )

        self.assertEqual(
            [item.id for item in history],
            [newest.id, middle.id, oldest.id],
        )

    def test_get_history_returns_empty_queryset_without_analyses(self):
        history = AnalysisHistoryService.get_history(self.repository)

        self.assertEqual(history.count(), 0)

    def test_get_latest_returns_most_recent_analysis(self):
        self.create_analysis(40, self.now - timedelta(days=2))
        newest = self.create_analysis(90, self.now - timedelta(days=1))

        result = AnalysisHistoryService.get_latest(self.repository)

        self.assertEqual(result.id, newest.id)

    def test_get_latest_returns_none_without_analyses(self):
        result = AnalysisHistoryService.get_latest(self.repository)

        self.assertIsNone(result)

    def test_get_previous_returns_second_most_recent_analysis(self):
        self.create_analysis(40, self.now - timedelta(days=3))
        previous = self.create_analysis(70, self.now - timedelta(days=2))
        self.create_analysis(90, self.now - timedelta(days=1))

        result = AnalysisHistoryService.get_previous(self.repository)

        self.assertEqual(result.id, previous.id)

    def test_get_previous_returns_none_with_fewer_than_two_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_previous(self.repository)
        )

        self.create_analysis(70)

        self.assertIsNone(
            AnalysisHistoryService.get_previous(self.repository)
        )

    def test_get_best_returns_highest_overall_score(self):
        self.create_analysis(40)
        best = self.create_analysis(95)
        self.create_analysis(70)

        result = AnalysisHistoryService.get_best(self.repository)

        self.assertEqual(result.id, best.id)

    def test_get_worst_returns_lowest_overall_score(self):
        self.create_analysis(80)
        worst = self.create_analysis(20)
        self.create_analysis(60)

        result = AnalysisHistoryService.get_worst(self.repository)

        self.assertEqual(result.id, worst.id)

    def test_get_best_returns_none_without_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_best(self.repository)
        )

    def test_get_worst_returns_none_without_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_worst(self.repository)
        )

    def test_best_score_tie_prefers_most_recent_analysis(self):
        older = self.create_analysis(
            90,
            self.now - timedelta(days=2),
        )
        newer = self.create_analysis(
            90,
            self.now - timedelta(days=1),
        )

        result = AnalysisHistoryService.get_best(self.repository)

        self.assertEqual(result.id, newer.id)

    def test_worst_score_tie_prefers_most_recent_analysis(self):
        older = self.create_analysis(
            20,
            self.now - timedelta(days=2),
        )
        newer = self.create_analysis(
            20,
            self.now - timedelta(days=1),
        )

        result = AnalysisHistoryService.get_worst(self.repository)

        self.assertEqual(result.id, newer.id)

    def test_history_uses_id_to_break_equal_timestamp_ties(self):
        first = self.create_analysis(40, self.now)
        second = self.create_analysis(60, self.now)

        history = list(
            AnalysisHistoryService.get_history(self.repository)
        )

        self.assertEqual(
            [item.id for item in history],
            [second.id, first.id],
        )

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from api.models.repository import Repository
from api.models.analysis import Analysis
from api.services.analysis_history_service import AnalysisHistoryService


class AnalysisHistoryServiceTests(TestCase):
    """Tests for repository analysis history queries."""

    def setUp(self):
        self.now = timezone.now()

        self.repository = Repository.objects.create(
            github_id=10001,
            owner="test-owner",
            name="test-repository",
            full_name="test-owner/test-repository",
            description="Repository used for history tests",
            topics=["python", "django"],
            html_url="https://github.com/test-owner/test-repository",
            language="Python",
            license_name="MIT License",
            default_branch="main",
            stars=100,
            forks=10,
            watchers=100,
            open_issues=5,
            github_created_at=self.now - timedelta(days=365),
            github_updated_at=self.now,
        )

    def create_analysis(self, overall_score, created_at=None):
        analysis = Analysis.objects.create(
            repository=self.repository,
            project_type="Backend",
            popularity_score=overall_score,
            activity_score=overall_score,
            documentation_score=overall_score,
            maintainability_score=overall_score,
            code_quality_score=overall_score,
            community_score=overall_score,
            overall_score=overall_score,
        )

        if created_at is not None:
            Analysis.objects.filter(pk=analysis.pk).update(
                created_at=created_at
            )
            analysis.refresh_from_db()

        return analysis

    def test_get_history_returns_newest_first(self):
        oldest = self.create_analysis(
            40,
            self.now - timedelta(days=3),
        )
        newest = self.create_analysis(
            90,
            self.now - timedelta(days=1),
        )
        middle = self.create_analysis(
            60,
            self.now - timedelta(days=2),
        )

        history = list(
            AnalysisHistoryService.get_history(self.repository)
        )

        self.assertEqual(
            [item.id for item in history],
            [newest.id, middle.id, oldest.id],
        )

    def test_get_history_returns_empty_queryset_without_analyses(self):
        history = AnalysisHistoryService.get_history(self.repository)

        self.assertEqual(history.count(), 0)

    def test_get_latest_returns_most_recent_analysis(self):
        self.create_analysis(40, self.now - timedelta(days=2))
        newest = self.create_analysis(90, self.now - timedelta(days=1))

        result = AnalysisHistoryService.get_latest(self.repository)

        self.assertEqual(result.id, newest.id)

    def test_get_latest_returns_none_without_analyses(self):
        result = AnalysisHistoryService.get_latest(self.repository)

        self.assertIsNone(result)

    def test_get_previous_returns_second_most_recent_analysis(self):
        self.create_analysis(40, self.now - timedelta(days=3))
        previous = self.create_analysis(70, self.now - timedelta(days=2))
        self.create_analysis(90, self.now - timedelta(days=1))

        result = AnalysisHistoryService.get_previous(self.repository)

        self.assertEqual(result.id, previous.id)

    def test_get_previous_returns_none_with_fewer_than_two_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_previous(self.repository)
        )

        self.create_analysis(70)

        self.assertIsNone(
            AnalysisHistoryService.get_previous(self.repository)
        )

    def test_get_best_returns_highest_overall_score(self):
        self.create_analysis(40)
        best = self.create_analysis(95)
        self.create_analysis(70)

        result = AnalysisHistoryService.get_best(self.repository)

        self.assertEqual(result.id, best.id)

    def test_get_worst_returns_lowest_overall_score(self):
        self.create_analysis(80)
        worst = self.create_analysis(20)
        self.create_analysis(60)

        result = AnalysisHistoryService.get_worst(self.repository)

        self.assertEqual(result.id, worst.id)

    def test_get_best_returns_none_without_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_best(self.repository)
        )

    def test_get_worst_returns_none_without_analyses(self):
        self.assertIsNone(
            AnalysisHistoryService.get_worst(self.repository)
        )

    def test_best_score_tie_prefers_most_recent_analysis(self):
        older = self.create_analysis(
            90,
            self.now - timedelta(days=2),
        )
        newer = self.create_analysis(
            90,
            self.now - timedelta(days=1),
        )

        result = AnalysisHistoryService.get_best(self.repository)

        self.assertEqual(result.id, newer.id)

    def test_worst_score_tie_prefers_most_recent_analysis(self):
        older = self.create_analysis(
            20,
            self.now - timedelta(days=2),
        )
        newer = self.create_analysis(
            20,
            self.now - timedelta(days=1),
        )

        result = AnalysisHistoryService.get_worst(self.repository)

        self.assertEqual(result.id, newer.id)

    def test_history_uses_id_to_break_equal_timestamp_ties(self):
        first = self.create_analysis(40, self.now)
        second = self.create_analysis(60, self.now)

        history = list(
            AnalysisHistoryService.get_history(self.repository)
        )

        self.assertEqual(
            [item.id for item in history],
            [second.id, first.id],
        )
