from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from api.services.ai_service import AIClient, AIServiceError

SETTINGS = "api.services.ai_service.settings"
POST = "api.services.ai_service.requests.post"


def response(status=200, payload=None, json_error=False):
    mock = MagicMock()
    mock.status_code = status
    if json_error:
        mock.json.side_effect = ValueError("not json")
    else:
        mock.json.return_value = payload
    return mock


OK = {
    "content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}],
    "stop_reason": "end_turn",
}


class ConfigurationTests(SimpleTestCase):

    def test_enabled_needs_the_flag_and_a_key(self):
        cases = [
            (True, "sk-key", True),
            ("true", "sk-key", True),
            (True, "", False),
            (True, None, False),
            (False, "sk-key", False),
            ("false", "sk-key", False),
        ]

        for flag, key, expected in cases:
            with self.subTest(flag=flag, key=key):
                with patch(
                    SETTINGS,
                    AI_SUMMARY_ENABLED=flag,
                    ANTHROPIC_API_KEY=key,
                ):
                    self.assertEqual(AIClient.is_enabled(), expected)

    def test_model_must_look_like_a_model_name(self):
        with patch(SETTINGS, AI_MODEL="claude-haiku-5-5"):
            self.assertEqual(AIClient.model(), "claude-haiku-5-5")

        with patch(SETTINGS, AI_MODEL="bad model\nname"):
            self.assertEqual(AIClient.model(), AIClient.DEFAULT_MODEL)

    def test_numbers_are_limited(self):
        with patch(SETTINGS, AI_TIMEOUT_SECONDS="999", AI_MAX_TOKENS="1"):
            self.assertEqual(AIClient.timeout(), 60)
            self.assertEqual(AIClient.max_tokens(), 50)

        with patch(SETTINGS, AI_TIMEOUT_SECONDS="soon", AI_MAX_TOKENS=None):
            self.assertEqual(AIClient.timeout(), 20)
            self.assertEqual(AIClient.max_tokens(), 500)


class CompleteTests(SimpleTestCase):

    def call(self, **kwargs):
        with patch(
            SETTINGS,
            spec=[],
            ANTHROPIC_API_KEY="sk-secret",
            AI_MODEL="m1",
        ):
            return AIClient.complete("system text", "user text")

    def test_request_is_built_safely(self):
        with patch(POST, return_value=response(payload=OK)) as post:
            result = self.call()

        self.assertEqual(result, {"text": "Hello world", "truncated": False})

        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.anthropic.com/v1/messages")
        self.assertEqual(kwargs["headers"]["x-api-key"], "sk-secret")
        self.assertEqual(kwargs["json"]["model"], "m1")
        self.assertEqual(kwargs["json"]["system"], "system text")
        self.assertEqual(
            kwargs["json"]["messages"],
            [{"role": "user", "content": "user text"}],
        )
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["timeout"], 20)

    def test_truncated_answers_are_flagged(self):
        payload = dict(OK, stop_reason="max_tokens")

        with patch(POST, return_value=response(payload=payload)):
            self.assertTrue(self.call()["truncated"])

    def test_missing_key_fails_without_calling(self):
        with patch(SETTINGS, ANTHROPIC_API_KEY=""):
            with patch(POST) as post:
                with self.assertRaises(AIServiceError):
                    AIClient.complete("s", "u")

        post.assert_not_called()

    def test_network_errors_become_ai_errors(self):
        for error in (requests.Timeout(), requests.ConnectionError()):
            with self.subTest(error=type(error).__name__):
                with patch(POST, side_effect=error):
                    with self.assertRaises(AIServiceError):
                        self.call()

    def test_error_statuses_become_ai_errors(self):
        for status in (400, 401, 429, 500, 529):
            with self.subTest(status=status):
                with patch(POST, return_value=response(status=status)):
                    with self.assertRaises(AIServiceError) as context:
                        self.call()

                self.assertIn(str(status), str(context.exception))

    def test_unexpected_bodies_become_ai_errors(self):
        for mock in (
            response(json_error=True),
            response(payload={}),
            response(payload={"content": "text"}),
            response(payload=None),
            response(payload=[1]),
        ):
            with self.subTest(body=mock.json.return_value):
                with patch(POST, return_value=mock):
                    with self.assertRaises(AIServiceError):
                        self.call()

    def test_the_key_never_appears_in_errors(self):
        with patch(POST, side_effect=requests.ConnectionError("sk-secret")):
            with self.assertRaises(AIServiceError) as context:
                self.call()

        self.assertNotIn("sk-secret", str(context.exception))
