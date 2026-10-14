
from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.release_analysis_service import ReleaseAnalysisService


class ReleaseAnalysisServiceTests(SimpleTestCase):

    def test_get_releases_returns_only_dictionaries(self):
        response = [
            {"tag_name": "v2.0.0"},
            "invalid release",
            None,
            {"tag_name": "v1.0.0"},
        ]

        with patch(
            "api.services.release_analysis_service.GitHubService.request",
            return_value=response,
        ):
            result = ReleaseAnalysisService.get_releases(
                "owner",
                "repository",
            )

        self.assertEqual(
            result,
            [
                {"tag_name": "v2.0.0"},
                {"tag_name": "v1.0.0"},
            ],
        )

    def test_get_releases_returns_empty_list_on_error(self):
        with patch(
            "api.services.release_analysis_service.GitHubService.request",
            side_effect=Exception("GitHub request failed"),
        ):
            result = ReleaseAnalysisService.get_releases(
                "owner",
                "repository",
            )

        self.assertEqual(result, [])

    def test_get_releases_handles_unexpected_response(self):
        with patch(
            "api.services.release_analysis_service.GitHubService.request",
            return_value={"message": "Not Found"},
        ):
            result = ReleaseAnalysisService.get_releases(
                "owner",
                "repository",
            )

        self.assertEqual(result, [])

    def test_serialize_release_builds_correct_url(self):
        release = {
            "name": "Version 2",
            "tag_name": "v2.0.0",
            "published_at": "2026-01-15T10:00:00Z",
            "draft": False,
            "prerelease": False,
        }

        result = ReleaseAnalysisService.serialize_release(
            release,
            "facebook",
            "react",
        )

        self.assertEqual(
            result["html_url"],
            "https://github.com/facebook/react/releases/tag/v2.0.0",
        )
        self.assertEqual(result["name"], "Version 2")
        self.assertEqual(result["tag_name"], "v2.0.0")
        self.assertFalse(result["draft"])
        self.assertFalse(result["prerelease"])

    def test_serialize_release_encodes_tag_name(self):
        release = {"tag_name": "release/2.0 beta"}

        result = ReleaseAnalysisService.serialize_release(
            release,
            "owner",
            "repository",
        )

        self.assertEqual(
            result["html_url"],
            "https://github.com/owner/repository/releases/tag/"
            "release%2F2.0%20beta",
        )

    def test_serialize_release_handles_missing_tag(self):
        result = ReleaseAnalysisService.serialize_release(
            {},
            "owner",
            "repository",
        )

        self.assertIsNone(result["html_url"])
        self.assertIsNone(result["tag_name"])
        self.assertFalse(result["draft"])
        self.assertFalse(result["prerelease"])

    def test_summarize_empty_releases(self):
        result = ReleaseAnalysisService.summarize(
            [],
            "owner",
            "repository",
        )

        self.assertEqual(result["total_releases"], 0)
        self.assertIsNone(result["latest_release"])
        self.assertEqual(result["releases"], [])

    def test_summarize_uses_first_release_as_latest(self):
        releases = [
            {"tag_name": "v2.0.0"},
            {"tag_name": "v1.0.0"},
        ]

        result = ReleaseAnalysisService.summarize(
            releases,
            "owner",
            "repository",
        )

        self.assertEqual(result["total_releases"], 2)
        self.assertEqual(
            result["latest_release"]["tag_name"],
            "v2.0.0",
        )
        self.assertEqual(
            result["releases"][1]["tag_name"],
            "v1.0.0",
        )

    def test_analyze_fetches_and_summarizes_releases(self):
        releases = [
            {"tag_name": "v3.0.0"},
            {"tag_name": "v2.0.0"},
        ]

        with patch(
            "api.services.release_analysis_service.GitHubService.request",
            return_value=releases,
        ) as mock_request:
            result = ReleaseAnalysisService.analyze(
                "owner",
                "repository",
            )

        mock_request.assert_called_once_with(
            "/repos/owner/repository/releases",
        )
        self.assertEqual(result["total_releases"], 2)
        self.assertEqual(
            result["latest_release"]["tag_name"],
            "v3.0.0",
        )
