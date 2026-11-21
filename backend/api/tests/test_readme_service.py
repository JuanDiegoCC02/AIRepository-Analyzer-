import base64
from unittest.mock import patch

from django.test import SimpleTestCase

from api.exceptions.github_exceptions import (
    GitHubAuthenticationError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubRequestError,
)
from api.services.readme_service import ReadmeService

REQUEST = "api.services.readme_service.GitHubService.request"

CONTENT = "# Title\n\nSome words here.\n\n## Install\n\nRun it.\n"


def github_readme(content=CONTENT):
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    return {
        "name": "README.md",
        "path": "README.md",
        "size": len(content),
        "download_url": "https://example.org/README.md",
        "content": encoded,
    }


class GetReadmeTests(SimpleTestCase):

    def test_decodes_the_content(self):
        with patch(REQUEST, return_value=github_readme()) as mock_request:
            result = ReadmeService.get_readme("owner", "repo")

        mock_request.assert_called_once_with("/repos/owner/repo/readme")
        self.assertEqual(result["content"], CONTENT)
        self.assertEqual(result["name"], "README.md")

    def test_missing_readme_returns_none(self):
        with patch(REQUEST, side_effect=GitHubNotFoundError("missing")):
            self.assertIsNone(ReadmeService.get_readme("owner", "repo"))

    def test_other_github_errors_are_not_hidden(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            with self.assertRaises(GitHubRateLimitError):
                ReadmeService.get_readme("owner", "repo")

    def test_unexpected_responses_raise_a_request_error(self):
        broken = [
            ["not", "a", "dict"],
            "text",
            None,
            {"name": "README.md"},
            {"content": 5},
            {"content": "abc"},  # invalid base64 padding
        ]

        for response in broken:
            with self.subTest(response=response):
                with patch(REQUEST, return_value=response):
                    with self.assertRaises(GitHubRequestError):
                        ReadmeService.get_readme("owner", "repo")

    def test_missing_optional_fields_do_not_crash(self):
        data = {"content": github_readme()["content"]}

        with patch(REQUEST, return_value=data):
            result = ReadmeService.get_readme("owner", "repo")

        self.assertEqual(result["content"], CONTENT)
        self.assertIsNone(result["name"])
        self.assertEqual(result["size"], 0)


class AnalyzeTests(SimpleTestCase):

    def test_analyze_counts_words_and_headings(self):
        result = ReadmeService.analyze(
            {"content": CONTENT, "size": 50}
        )

        self.assertTrue(result["available"])
        self.assertTrue(result["exists"])
        self.assertEqual(result["size"], 50)
        self.assertEqual(result["sections"], 2)
        self.assertEqual(result["word_count"], len(CONTENT.split()))

    def test_analyze_without_readme(self):
        result = ReadmeService.analyze(None)

        self.assertEqual(
            result,
            {
                "available": True,
                "exists": False,
                "size": 0,
                "word_count": 0,
                "sections": 0,
            },
        )

    def test_unavailable_analysis(self):
        result = ReadmeService.unavailable()

        self.assertFalse(result["available"])
        self.assertIsNone(result["exists"])


class LoadAnalysisTests(SimpleTestCase):

    def test_existing_readme(self):
        with patch(REQUEST, return_value=github_readme()):
            result = ReadmeService.load_analysis("owner", "repo")

        self.assertTrue(result["available"])
        self.assertTrue(result["exists"])

    def test_missing_readme_is_a_real_result(self):
        with patch(REQUEST, side_effect=GitHubNotFoundError("missing")):
            result = ReadmeService.load_analysis("owner", "repo")

        self.assertTrue(result["available"])
        self.assertFalse(result["exists"])

    def test_github_failure_marks_the_analysis_as_unavailable(self):
        for error in (GitHubAuthenticationError("forbidden"),
                      GitHubRequestError("network")):
            with self.subTest(error=type(error).__name__):
                with patch(REQUEST, side_effect=error):
                    result = ReadmeService.load_analysis("owner", "repo")

                self.assertFalse(result["available"])

    def test_rate_limit_stops_the_analysis(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            with self.assertRaises(GitHubRateLimitError):
                ReadmeService.load_analysis("owner", "repo")
