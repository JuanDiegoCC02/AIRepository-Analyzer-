from datetime import datetime, timezone
from unittest.mock import patch

from django.test import SimpleTestCase

from api.exceptions.github_exceptions import (
    GitHubRateLimitError,
    GitHubRequestError,
)
from api.services.commits_service import CommitsService


def make_commit(
    login=None,
    name=None,
    date="2026-11-01T10:00:00Z",
    user_type="User",
):
    return {
        "author": (
            {"login": login, "type": user_type}
            if login
            else None
        ),
        "commit": {
            "author": {"name": name, "date": date},
            "committer": {"date": date},
        },
    }


class CommitsServiceTests(SimpleTestCase):

    def test_summarize_counts_humans_bots_and_authors(self):
        commits = [
            make_commit("alice", date="2026-11-05T10:00:00Z"),
            make_commit("alice", date="2026-11-01T10:00:00Z"),
            make_commit("bob", date="2026-10-20T10:00:00Z"),
            make_commit(
                "dependabot[bot]",
                user_type="Bot",
                date="2026-11-04T10:00:00Z",
            ),
            make_commit(None, name="Carol", date="2026-10-10T10:00:00Z"),
            make_commit(None, name=None, date="2026-10-01T10:00:00Z"),
        ]

        result = CommitsService.summarize(commits)

        self.assertTrue(result["available"])
        self.assertEqual(result["commits"], 5)
        self.assertEqual(result["bot_commits"], 1)
        self.assertEqual(result["active_authors"], 3)
        self.assertEqual(result["last_commit_at"], "2026-11-05T10:00:00Z")
        self.assertFalse(result["capped"])

    def test_summarize_marks_result_as_capped_at_page_size(self):
        commits = [make_commit("alice") for _ in range(100)]

        result = CommitsService.summarize(commits)

        self.assertTrue(result["capped"])
        self.assertEqual(result["commits"], 100)

    def test_summarize_returns_unavailable_when_commits_are_none(self):
        result = CommitsService.summarize(None)

        self.assertFalse(result["available"])
        self.assertEqual(result["commits"], 0)
        self.assertIsNone(result["last_commit_at"])

    def test_summarize_handles_zero_commits_as_available(self):
        result = CommitsService.summarize([])

        self.assertTrue(result["available"])
        self.assertEqual(result["commits"], 0)
        self.assertIsNone(result["last_commit_at"])

    def test_summarize_ignores_invalid_dates(self):
        result = CommitsService.summarize(
            [make_commit("alice", date="not-a-date")]
        )

        self.assertEqual(result["commits"], 1)
        self.assertIsNone(result["last_commit_at"])

    def test_get_recent_commits_filters_non_dictionary_items(self):
        with patch(
            "api.services.commits_service.GitHubService.request",
            return_value=[None, "invalid", make_commit("alice")],
        ):
            result = CommitsService.get_recent_commits("owner", "repo")

        self.assertEqual(len(result), 1)

    def test_get_recent_commits_returns_none_on_github_error(self):
        with patch(
            "api.services.commits_service.GitHubService.request",
            side_effect=GitHubRequestError("network"),
        ):
            result = CommitsService.analyze("owner", "repo")

        self.assertFalse(result["available"])

    def test_rate_limit_stops_the_analysis_instead_of_hiding_it(self):
        with patch(
            "api.services.commits_service.GitHubService.request",
            side_effect=GitHubRateLimitError("rate limit", retry_after=30),
        ):
            with self.assertRaises(GitHubRateLimitError):
                CommitsService.analyze("owner", "repo")

    def test_get_recent_commits_returns_none_for_unexpected_response(self):
        with patch(
            "api.services.commits_service.GitHubService.request",
            return_value={"message": "unexpected"},
        ):
            result = CommitsService.analyze("owner", "repo")

        self.assertFalse(result["available"])

    def test_analyze_requests_the_ninety_day_window(self):
        now = datetime(2026, 11, 9, tzinfo=timezone.utc)

        with patch(
            "api.services.commits_service.GitHubService.request",
            return_value=[],
        ) as mock_request:
            CommitsService.analyze("owner", "repo", now=now)

        mock_request.assert_called_once_with(
            "/repos/owner/repo/commits",
            params={
                "since": "2026-08-11T00:00:00Z",
                "per_page": 100,
            },
        )
