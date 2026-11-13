from unittest.mock import patch

from django.test import SimpleTestCase

from api.exceptions.github_exceptions import (
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from api.services.repository_structure_service import (
    RepositoryStructureService,
)

REQUEST = "api.services.repository_structure_service.GitHubService.request"


def listing(*items):
    return [{"name": name, "type": item_type} for name, item_type in items]


ROOT = listing(
    ("README.md", "file"),
    (".github", "dir"),
    ("Tests", "dir"),
)

WORKFLOWS = listing(
    ("Tests.YAML", "file"),
    ("lint.yml", "file"),
    ("notes.md", "file"),
    ("nested.yml", "dir"),
)


class RepositoryStructureServiceTests(SimpleTestCase):

    def test_get_root_entries_normalizes_names_to_lowercase(self):
        with patch(REQUEST, return_value=ROOT) as mock_request:
            result = RepositoryStructureService.get_root_entries(
                "owner",
                "repo",
            )

        mock_request.assert_called_once_with("/repos/owner/repo/contents")
        self.assertEqual(
            result,
            {"readme.md": "file", ".github": "dir", "tests": "dir"},
        )

    def test_get_root_entries_ignores_malformed_items(self):
        items = [
            None, "text", 5, {"name": "ok.txt", "type": "file"},
            {"name": 7, "type": "file"}, {"name": "x"},
            {"name": "", "type": "file"},
            {"name": "a" * 300, "type": "file"},
        ]

        with patch(REQUEST, return_value=items):
            result = RepositoryStructureService.get_root_entries(
                "owner",
                "repo",
            )

        self.assertEqual(result, {"ok.txt": "file"})

    def test_get_root_entries_limits_the_number_of_entries(self):
        items = [
            {"name": f"file{index}", "type": "file"}
            for index in range(RepositoryStructureService.MAX_ENTRIES + 50)
        ]

        with patch(REQUEST, return_value=items):
            result = RepositoryStructureService.get_root_entries(
                "owner",
                "repo",
            )

        self.assertEqual(
            len(result),
            RepositoryStructureService.MAX_ENTRIES,
        )

    def test_empty_repository_returns_empty_entries(self):
        with patch(REQUEST, side_effect=GitHubNotFoundError("empty")):
            result = RepositoryStructureService.get_root_entries(
                "owner",
                "repo",
            )

        self.assertEqual(result, {})

    def test_github_errors_return_none(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            result = RepositoryStructureService.get_root_entries(
                "owner",
                "repo",
            )

        self.assertIsNone(result)

    def test_unexpected_response_returns_none(self):
        for response in ({"message": "x"}, "text", None, 5):
            with self.subTest(response=response):
                with patch(REQUEST, return_value=response):
                    result = RepositoryStructureService.get_root_entries(
                        "owner",
                        "repo",
                    )

                self.assertIsNone(result)

    def test_get_workflow_files_keeps_only_yaml_files(self):
        with patch(REQUEST, return_value=WORKFLOWS) as mock_request:
            result = RepositoryStructureService.get_workflow_files(
                "owner",
                "repo",
            )

        mock_request.assert_called_once_with(
            "/repos/owner/repo/contents/.github/workflows"
        )
        self.assertEqual(sorted(result), ["lint.yml", "tests.yaml"])

    def test_missing_workflows_folder_means_no_workflows(self):
        with patch(REQUEST, side_effect=GitHubNotFoundError("missing")):
            result = RepositoryStructureService.get_workflow_files(
                "owner",
                "repo",
            )

        self.assertEqual(result, [])

    def test_workflow_errors_return_none(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            result = RepositoryStructureService.get_workflow_files(
                "owner",
                "repo",
            )

        self.assertIsNone(result)

    def test_analyze_reads_workflows_when_github_folder_exists(self):
        with patch(REQUEST, side_effect=[ROOT, WORKFLOWS]) as mock_request:
            result = RepositoryStructureService.analyze("owner", "repo")

        self.assertEqual(mock_request.call_count, 2)
        self.assertTrue(result["available"])
        self.assertEqual(
            sorted(result["workflows"]),
            ["lint.yml", "tests.yaml"],
        )

    def test_analyze_skips_workflows_request_without_github_folder(self):
        with patch(
            REQUEST,
            return_value=listing(("README.md", "file")),
        ) as mock_request:
            result = RepositoryStructureService.analyze("owner", "repo")

        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(result["workflows"], [])

    def test_analyze_is_unavailable_when_the_root_cannot_be_read(self):
        with patch(REQUEST, side_effect=GitHubRateLimitError("limit")):
            result = RepositoryStructureService.analyze("owner", "repo")

        self.assertFalse(result["available"])
        self.assertEqual(result["entries"], {})
        self.assertIsNone(result["workflows"])

    def test_analyze_keeps_root_when_only_workflows_fail(self):
        with patch(
            REQUEST,
            side_effect=[ROOT, GitHubRateLimitError("limit")],
        ):
            result = RepositoryStructureService.analyze("owner", "repo")

        self.assertTrue(result["available"])
        self.assertIsNone(result["workflows"])