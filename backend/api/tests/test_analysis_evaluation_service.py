
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from api.models.repository import Repository
from api.models.analysis import Analysis
from api.services.analysis_evaluation_service import AnalysisEvaluationService


User = get_user_model()


class AnalysisEvaluationServiceTests(TestCase):

    def setUp(self):
        now = timezone.now()

        self.repository = Repository.objects.create(
            github_id=123456,
            owner="facebook",
            name="react",
            full_name="facebook/react",
            html_url="https://github.com/facebook/react",
            github_created_at=now,
            github_updated_at=now,
        )

        self.user1 = User.objects.create_user(
            username="user1",
            password="test-password-123",
        )

        self.user2 = User.objects.create_user(
            username="user2",
            password="test-password-123",
        )

    def create_analysis(self, user, score):
        return Analysis.objects.create(
            repository=self.repository,
            user=user,
            project_type="Web Application",
            popularity_score=score,
            activity_score=score,
            documentation_score=score,
            maintainability_score=score,
            code_quality_score=score,
            community_score=score,
            overall_score=score,
        )

    def test_evaluation_uses_previous_analysis_from_same_user(self):
        previous = self.create_analysis(self.user1, 70)

        # This analysis belongs to another user.
        self.create_analysis(self.user2, 95)

        current = self.create_analysis(self.user1, 85)

        result = AnalysisEvaluationService.generate(
            self.repository,
            current,
        )

        self.assertTrue(result["available"])
        self.assertEqual(
            result["previous_analysis_id"],
            previous.id,
        )
        self.assertEqual(result["overall_trend"], "Improving")
        self.assertEqual(result["overall_difference"], 15)

    def test_evaluation_does_not_use_another_users_analysis(self):
        self.create_analysis(self.user2, 70)

        current = self.create_analysis(self.user1, 85)

        result = AnalysisEvaluationService.generate(
            self.repository,
            current,
        )

        self.assertFalse(result["available"])
        self.assertIsNone(result["comparison"])

    def test_anonymous_analysis_only_compares_with_anonymous_history(self):
        previous = self.create_analysis(None, 60)

        # This analysis belongs to an authenticated user.
        self.create_analysis(self.user1, 95)

        current = self.create_analysis(None, 80)

        result = AnalysisEvaluationService.generate(
            self.repository,
            current,
        )

        self.assertTrue(result["available"])
        self.assertEqual(
            result["previous_analysis_id"],
            previous.id,
        )
        self.assertEqual(result["overall_difference"], 20)
