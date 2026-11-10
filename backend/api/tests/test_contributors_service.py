from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.contributors_service import ContributorsService


def make_contributors(count):
    return [
        {
            "login": f"user{index}",
            "contributions": count - index,
            "avatar_url": f"https://avatars.example/{index}",
            "html_url": f"https://github.com/user{index}",
        }
        for index in range(count)
    ]


class ContributorsServiceTests(SimpleTestCase):

    def test_get_contributors_requests_the_maximum_page_size(self):
        with patch(
            "api.services.contributors_service.GitHubService.request",
            return_value=[],
        ) as mock_request:
            ContributorsService.get_contributors("owner", "repo")

        mock_request.assert_called_once_with(
            "/repos/owner/repo/contributors",
            params={"per_page": 100},
        )

    def test_get_contributors_returns_only_dictionaries(self):
        with patch(
            "api.services.contributors_service.GitHubService.request",
            return_value=[{"login": "alice"}, None, "invalid", 3],
        ):
            result = ContributorsService.get_contributors("owner", "repo")

        self.assertEqual(result, [{"login": "alice"}])

    def test_get_contributors_returns_empty_list_on_error(self):
        with patch(
            "api.services.contributors_service.GitHubService.request",
            side_effect=Exception("GitHub request failed"),
        ):
            result = ContributorsService.get_contributors("owner", "repo")

        self.assertEqual(result, [])

    def test_get_contributors_returns_empty_list_for_unexpected_data(self):
        with patch(
            "api.services.contributors_service.GitHubService.request",
            return_value={"message": "unexpected"},
        ):
            result = ContributorsService.get_contributors("owner", "repo")

        self.assertEqual(result, [])

    def test_summarize_empty_contributors(self):
        result = ContributorsService.summarize([])

        self.assertEqual(result["total_contributors"], 0)
        self.assertFalse(result["capped"])
        self.assertIsNone(result["top_contributor"])
        self.assertEqual(result["contributors"], [])

    def test_summarize_orders_by_contributions(self):
        result = ContributorsService.summarize(
            [
                {"login": "small", "contributions": 2},
                {"login": "big", "contributions": 50},
                {"login": "medium", "contributions": 10},
            ]
        )

        self.assertEqual(result["total_contributors"], 3)
        self.assertEqual(result["top_contributor"], "big")
        self.assertEqual(result["top_contributions"], 50)
        self.assertEqual(
            [item["login"] for item in result["contributors"]],
            ["big", "medium", "small"],
        )
        self.assertFalse(result["capped"])

    def test_summarize_flags_a_full_page_as_capped(self):
        result = ContributorsService.summarize(make_contributors(100))

        self.assertEqual(result["total_contributors"], 100)
        self.assertTrue(result["capped"])

    def test_summarize_does_not_flag_a_partial_page_as_capped(self):
        result = ContributorsService.summarize(make_contributors(99))

        self.assertEqual(result["total_contributors"], 99)
        self.assertFalse(result["capped"])