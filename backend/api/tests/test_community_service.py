from django.test import SimpleTestCase

from api.services.community_service import CommunityService

# Real data from pallets/flask.
FLASK = {
    "stargazers_count": 75112,
    "forks_count": 17323,
    "subscribers_count": 2177,
    "open_issues_count": 4,
    "watchers_count": 75112,
}


class CommunityServiceTests(SimpleTestCase):

    def test_flask_scores_90(self):
        # stars 30 + forks 25 + subscribers 20 + issues 15
        self.assertEqual(CommunityService.calculate(FLASK), 90)

    def test_watchers_count_is_ignored_because_it_copies_the_stars(self):
        without = dict(FLASK)
        without.pop("watchers_count")

        self.assertEqual(
            CommunityService.calculate(FLASK),
            CommunityService.calculate(without),
        )

        huge = dict(FLASK, watchers_count=10**9)

        self.assertEqual(
            CommunityService.calculate(huge),
            CommunityService.calculate(FLASK),
        )

    def test_subscriber_bands(self):
        # stars < 1000 earn 10 points; the rest comes from subscribers.
        cases = [(0, 10), (49, 10), (50, 20), (299, 20),
                 (300, 25), (999, 25), (1000, 30)]

        for subscribers, expected in cases:
            with self.subTest(subscribers=subscribers):
                score = CommunityService.calculate(
                    {"subscribers_count": subscribers}
                )

                self.assertEqual(score, expected)

    def test_score_is_capped_at_100(self):
        score = CommunityService.calculate({
            "stargazers_count": 10**7,
            "forks_count": 10**6,
            "subscribers_count": 10**6,
            "open_issues_count": 0,
        })

        self.assertEqual(score, 100)

    def test_invalid_values_count_as_zero(self):
        score = CommunityService.calculate({
            "stargazers_count": None,
            "forks_count": "many",
            "subscribers_count": True,
            "open_issues_count": float("nan"),
        })

        self.assertEqual(score, 10)

    def test_invalid_repository_returns_zero(self):
        self.assertEqual(CommunityService.calculate(None), 0)
        self.assertEqual(CommunityService.calculate("text"), 0)

    def test_open_issues_bands(self):
        cases = [(0, 25), (100, 25), (101, 20), (500, 20), (501, 10)]

        for issues, expected in cases:
            with self.subTest(issues=issues):
                score = CommunityService.calculate(
                    {"open_issues_count": issues}
                )

                self.assertEqual(score, expected)
