from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase

from api.services.ai_insights_service import AIInsightsService
from api.services.ai_service import AIServiceError

BASE = "api.services.ai_insights_service"
ENABLED = f"{BASE}.AIClient.is_enabled"
COMPLETE = f"{BASE}.AIClient.complete"
SETTINGS = f"{BASE}.settings"
BUDGET = "api.services.ai_service.settings"

GOOD = (
    "The project has strong documentation and steady activity, while its "
    "popularity is the weakest area compared with the other scores."
)
SCORES = {"overall_score": 70}


def generate():
    return AIInsightsService.generate(
        {"name": "demo"},
        "Backend",
        [],
        SCORES,
        None,
    )


class AIInsightsServiceTests(SimpleTestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_returns_the_validated_summary(self):
        with patch(ENABLED, return_value=True):
            with patch(
                COMPLETE,
                return_value={"text": GOOD, "truncated": False},
            ) as complete:
                self.assertEqual(generate(), GOOD)

        system, message = complete.call_args.args
        self.assertIn("untrusted", system)
        self.assertIn("<repository_data>", message)

    def test_nothing_is_called_when_ai_is_disabled(self):
        with patch(ENABLED, return_value=False):
            with patch(COMPLETE) as complete:
                self.assertIsNone(generate())

        complete.assert_not_called()

    def test_provider_errors_return_none(self):
        with patch(ENABLED, return_value=True):
            with patch(COMPLETE, side_effect=AIServiceError("timeout")):
                with self.assertLogs(BASE, level="WARNING"):
                    self.assertIsNone(generate())

    def test_unexpected_errors_return_none(self):
        with patch(ENABLED, return_value=True):
            with patch(COMPLETE, side_effect=RuntimeError("boom")):
                with self.assertLogs(BASE, level="ERROR"):
                    self.assertIsNone(generate())

    def test_rejected_answers_return_none(self):
        bad = GOOD + " Read https://evil.example"

        with patch(ENABLED, return_value=True):
            with patch(
                COMPLETE,
                return_value={"text": bad, "truncated": False},
            ):
                with self.assertLogs(BASE, level="WARNING"):
                    self.assertIsNone(generate())

    def test_truncated_answers_return_none(self):
        with patch(ENABLED, return_value=True):
            with patch(
                COMPLETE,
                return_value={"text": GOOD, "truncated": True},
            ):
                with self.assertLogs(BASE, level="WARNING"):
                    self.assertIsNone(generate())

    def test_the_hourly_budget_limits_the_calls(self):
        with patch(ENABLED, return_value=True):
            with patch(BUDGET, AI_MAX_CALLS_PER_HOUR="2"):
                with patch(
                    COMPLETE,
                    return_value={"text": GOOD, "truncated": False},
                ) as complete:
                    results = [generate() for _ in range(3)]

        self.assertEqual(results, [GOOD, GOOD, None])
        self.assertEqual(complete.call_count, 2)

    def test_a_zero_budget_blocks_every_call(self):
        with patch(ENABLED, return_value=True):
            with patch(BUDGET, AI_MAX_CALLS_PER_HOUR="0"):
                with patch(COMPLETE) as complete:
                    self.assertIsNone(generate())

        complete.assert_not_called()

    def test_language_comes_from_the_settings(self):
        with patch(ENABLED, return_value=True):
            with patch(SETTINGS, AI_SUMMARY_LANGUAGE="Spanish"):
                with patch(
                    COMPLETE,
                    return_value={"text": GOOD, "truncated": False},
                ) as complete:
                    generate()

        self.assertIn("Spanish", complete.call_args.args[0])
