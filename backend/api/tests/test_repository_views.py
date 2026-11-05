from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from api.models.repository import Repository
from api.models.analysis import Analysis


User = get_user_model()


class RepositoryViewsTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create two independent users.
        self.user = User.objects.create_user(
            username="user_one",
            password="testpassword123",
        )

        self.other_user = User.objects.create_user(
            username="user_two",
            password="testpassword123",
        )

        # Authenticate the first user.
        self.client.force_authenticate(user=self.user)

        # Create a repository.
        self.repository = Repository.objects.create(
            github_id=123456,
            owner="facebook",
            name="react",
            full_name="facebook/react",
            description="React JavaScript library",
            topics=["javascript", "react"],
            html_url="https://github.com/facebook/react",
            language="JavaScript",
            license_name="MIT",
            default_branch="main",
            stars=100,
            forks=20,
            watchers=50,
            open_issues=10,
            github_created_at=timezone.now(),
            github_updated_at=timezone.now(),
        )

        # Create an analysis for the first user.
        self.analysis = Analysis.objects.create(
            repository=self.repository,
            user=self.user,
            project_type="Frontend",
            popularity_score=90,
            activity_score=85,
            documentation_score=80,
            maintainability_score=75,
            code_quality_score=88,
            community_score=90,
            overall_score=85,
            ai_summary="Test summary",
            recommendations="Test recommendation",
        )

    # --------------------------------------------------
    # Authentication tests
    # --------------------------------------------------

    def test_analyze_requires_authentication(self):

        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("repository-analyze"),
            {
                "repository_url": "https://github.com/facebook/react"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_repository_list_requires_authentication(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse("repository-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_repository_detail_requires_authentication(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                "repository-detail",
                kwargs={"repository_id": self.repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_repository_history_requires_authentication(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                "repository-history",
                kwargs={"repository_id": self.repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # --------------------------------------------------
    # Repository analyzer tests
    # --------------------------------------------------

    @patch(
        "api.views.repository_views.AnalyzerService.analyze_repository"
    )
    def test_analyze_repository_returns_success(self, mock_analyze):

        mock_analyze.return_value = {
            "message": "Analysis completed successfully"
        }

        response = self.client.post(
            reverse("repository-analyze"),
            {
                "repository_url": "https://github.com/facebook/react"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            {"message": "Analysis completed successfully"},
        )

        mock_analyze.assert_called_once_with(
            "https://github.com/facebook/react",
            user=self.user,
        )

    @patch(
        "api.views.repository_views.AnalyzerService.analyze_repository"
    )
    def test_analyze_repository_rejects_invalid_url(self, mock_analyze):

        response = self.client.post(
            reverse("repository-analyze"),
            {
                "repository_url": "https://gitlab.com/user/project"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        mock_analyze.assert_not_called()

    # --------------------------------------------------
    # Repository list tests
    # --------------------------------------------------

    def test_repository_list_returns_only_user_repositories(self):

        other_repository = Repository.objects.create(
            github_id=654321,
            owner="django",
            name="django",
            full_name="django/django",
            html_url="https://github.com/django/django",
            github_created_at=timezone.now(),
            github_updated_at=timezone.now(),
        )

        Analysis.objects.create(
            repository=other_repository,
            user=self.other_user,
            project_type="Backend",
        )

        response = self.client.get(
            reverse("repository-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["count"], 1)

        self.assertEqual(
            response.data["repositories"][0]["full_name"],
            "facebook/react",
        )

    # --------------------------------------------------
    # Repository detail tests
    # --------------------------------------------------

    def test_repository_detail_returns_user_analysis(self):

        Analysis.objects.create(
            repository=self.repository,
            user=self.other_user,
            project_type="Frontend",
            overall_score=70,
        )

        response = self.client.get(
            reverse(
                "repository-detail",
                kwargs={"repository_id": self.repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["analyses_count"],
            1,
        )

    def test_repository_detail_returns_404_for_other_user(self):

        other_repository = Repository.objects.create(
            github_id=789012,
            owner="python",
            name="cpython",
            full_name="python/cpython",
            html_url="https://github.com/python/cpython",
            github_created_at=timezone.now(),
            github_updated_at=timezone.now(),
        )

        Analysis.objects.create(
            repository=other_repository,
            user=self.other_user,
            project_type="Backend",
        )

        response = self.client.get(
            reverse(
                "repository-detail",
                kwargs={"repository_id": other_repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --------------------------------------------------
    # Repository history tests
    # --------------------------------------------------

    def test_repository_history_returns_user_analyses(self):

        Analysis.objects.create(
            repository=self.repository,
            user=self.other_user,
            project_type="Frontend",
            overall_score=70,
        )

        response = self.client.get(
            reverse(
                "repository-history",
                kwargs={"repository_id": self.repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(response.data["count"], 1)

        self.assertEqual(
            response.data["repository"],
            "facebook/react",
        )

    def test_repository_history_returns_404_for_other_user(self):

        other_repository = Repository.objects.create(
            github_id=987654,
            owner="pallets",
            name="flask",
            full_name="pallets/flask",
            html_url="https://github.com/pallets/flask",
            github_created_at=timezone.now(),
            github_updated_at=timezone.now(),
        )

        Analysis.objects.create(
            repository=other_repository,
            user=self.other_user,
            project_type="Backend",
        )

        response = self.client.get(
            reverse(
                "repository-history",
                kwargs={"repository_id": other_repository.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )