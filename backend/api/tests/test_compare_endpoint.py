from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from api.throttles import CompareRateThrottle

ANALYZE = (
    "api.services.repository_comparison_service."
    "AnalyzerService.analyze_repository"
)

User = get_user_model()

DIMENSIONS = (
    "popularity",
    "activity",
    "documentation",
    "maintainability",
    "code_quality",
    "community",
)


def analysis_result(name, overall):
    scores = {f"{d}_score": 70 for d in DIMENSIONS}
    scores["overall_score"] = overall
    scores.update({"id": 1, "score_version": 5})

    return {
        "repository": {
            "id": 1,
            "full_name": name,
            "html_url": f"https://github.com/{name}",
            "description": None,
            "language": "Python",
            "stars": 1,
            "forks": 1,
        },
        "analysis": scores,
        "analysis_result": {"overall": {"score": overall, "level": "Good"}},
        "classification": {"project_type": "Backend"},
        "data_quality": {"complete": True, "missing": []},
    }


class CompareEndpointTests(TestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("repository-compare")
        self.urls = [
            "https://github.com/a/one",
            "https://github.com/b/two",
        ]

    def post(self, urls=None, **patch_kwargs):
        payload = {"repository_urls": urls or self.urls}

        with patch(ANALYZE, **patch_kwargs) as mock_analyze:
            response = self.client.post(self.url, payload, format="json")

        self.mock_analyze = mock_analyze
        return response

    def test_authentication_is_required(self):
        client = APIClient()

        response = client.post(
            self.url,
            {"repository_urls": self.urls},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_post_is_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_successful_comparison(self):
        results = {
            self.urls[0]: analysis_result("a/one", 90),
            self.urls[1]: analysis_result("b/two", 60),
        }

        response = self.post(
            side_effect=lambda url, user=None: results[url],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["best_overall"], "a/one")
        self.assertEqual(len(response.data["repositories"]), 2)
        self.assertEqual(
            set(response.data["dimensions"]),
            set(DIMENSIONS),
        )
        self.assertEqual(self.mock_analyze.call_count, 2)

        for call in self.mock_analyze.call_args_list:
            self.assertEqual(call.kwargs["user"], self.user)

    def test_invalid_payload_returns_400_without_analyzing(self):
        for urls in (
            ["https://github.com/a/one"],
            ["https://github.com/a/one", "https://github.com/a/one"],
            ["https://github.com/a/one", "http://github.com/a/two"],
        ):
            with self.subTest(urls=urls):
                response = self.post(urls=urls)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.mock_analyze.assert_not_called()

    def test_not_found_says_which_repository(self):
        def analyze(url, user=None):
            if url == self.urls[1]:
                raise GitHubNotFoundError("hidden detail")

            return analysis_result("a/one", 80)

        response = self.post(side_effect=analyze)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error"]["code"],
            "github_repository_not_found",
        )
        self.assertEqual(
            response.data["error"]["repository_url"],
            self.urls[1],
        )
        self.assertNotIn("hidden detail", str(response.data))

    def test_rate_limit_returns_503_with_retry_after(self):
        response = self.post(
            side_effect=GitHubRateLimitError("limit", retry_after=42),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertEqual(response["Retry-After"], "42")

    def test_the_endpoint_is_throttled(self):
        with patch.object(CompareRateThrottle, "rate", "2/hour"):
            statuses = [
                self.post(
                    side_effect=lambda url, user=None: analysis_result(
                        "a/one", 70
                    ),
                ).status_code
                for _ in range(3)
            ]

        self.assertEqual(statuses[:2], [200, 200])
        self.assertEqual(statuses[2], status.HTTP_429_TOO_MANY_REQUESTS)
