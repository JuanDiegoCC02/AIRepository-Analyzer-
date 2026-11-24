from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import SimpleTestCase

from api.services.resources_cache_service import ResourcesCacheService

SETTINGS = "api.services.resources_cache_service.settings"


def resources(**changes):
    data = {
        "technologies": {"languages": []},
        "readme": {"available": True, "exists": True},
        "contributors": {"total_contributors": 1},
        "releases": {"total_releases": 0},
        "commits": {"available": True, "commits": 3},
        "structure": {"available": True, "entries": {}, "workflows": []},
    }
    data.update(changes)
    return data


class ResourcesCacheServiceTests(SimpleTestCase):

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    # --------------------------------------------------
    # Time to live
    # --------------------------------------------------

    def test_ttl_defaults_to_900_seconds(self):
        with patch(SETTINGS, spec=[]):
            self.assertEqual(ResourcesCacheService.ttl(), 900)

    def test_ttl_reads_the_setting_even_when_it_is_a_string(self):
        for value, expected in (("120", 120), (60, 60), ("0", 0), (0, 0)):
            with self.subTest(value=value):
                with patch(
                    SETTINGS,
                    GITHUB_RESOURCES_CACHE_SECONDS=value,
                ):
                    self.assertEqual(ResourcesCacheService.ttl(), expected)

    def test_invalid_ttl_uses_the_default(self):
        for value in ("soon", None, True, [5], ""):
            with self.subTest(value=value):
                with patch(
                    SETTINGS,
                    GITHUB_RESOURCES_CACHE_SECONDS=value,
                ):
                    self.assertEqual(ResourcesCacheService.ttl(), 900)

    def test_ttl_is_limited(self):
        with patch(SETTINGS, GITHUB_RESOURCES_CACHE_SECONDS="-30"):
            self.assertEqual(ResourcesCacheService.ttl(), 0)

        with patch(SETTINGS, GITHUB_RESOURCES_CACHE_SECONDS="99999999"):
            self.assertEqual(
                ResourcesCacheService.ttl(),
                ResourcesCacheService.MAX_TTL,
            )

    # --------------------------------------------------
    # Keys
    # --------------------------------------------------

    def test_key_changes_with_the_repository_and_the_push_date(self):
        first = ResourcesCacheService.build_key(1, "2026-10-01T00:00:00Z")
        same = ResourcesCacheService.build_key(1, "2026-10-01T00:00:00Z")
        pushed = ResourcesCacheService.build_key(1, "2026-10-02T00:00:00Z")
        other = ResourcesCacheService.build_key(2, "2026-10-01T00:00:00Z")

        self.assertEqual(first, same)
        self.assertNotEqual(first, pushed)
        self.assertNotEqual(first, other)

    def test_key_only_contains_safe_characters(self):
        key = ResourcesCacheService.build_key(
            123,
            "evil key\n with spaces and \x00 control characters",
        )

        self.assertRegex(key, r"^[a-z0-9:\-]+$")
        self.assertNotIn(" ", key)

    def test_key_accepts_a_missing_push_date(self):
        self.assertIsNotNone(ResourcesCacheService.build_key(1, None))

    def test_key_requires_a_valid_repository_id(self):
        for github_id in (None, 0, -1, "12", 1.5, True, [1]):
            with self.subTest(github_id=github_id):
                self.assertIsNone(
                    ResourcesCacheService.build_key(github_id, "x")
                )

    # --------------------------------------------------
    # Complete results
    # --------------------------------------------------

    def test_complete_resources_are_accepted(self):
        self.assertTrue(ResourcesCacheService.is_complete(resources()))

    def test_unavailable_resources_are_not_complete(self):
        for name in ResourcesCacheService.REQUIRED_AVAILABLE:
            with self.subTest(name=name):
                self.assertFalse(
                    ResourcesCacheService.is_complete(
                        resources(**{name: {"available": False}})
                    )
                )

    def test_missing_or_malformed_resources_are_not_complete(self):
        self.assertFalse(ResourcesCacheService.is_complete(None))
        self.assertFalse(ResourcesCacheService.is_complete("text"))
        self.assertFalse(ResourcesCacheService.is_complete({}))

        without = resources()
        del without["contributors"]
        self.assertFalse(ResourcesCacheService.is_complete(without))

        self.assertFalse(
            ResourcesCacheService.is_complete(resources(commits=None))
        )
        self.assertFalse(
            ResourcesCacheService.is_complete(resources(commits={}))
        )

    # --------------------------------------------------
    # Reading and writing
    # --------------------------------------------------

    def test_saved_resources_can_be_read_back(self):
        data = resources()

        self.assertTrue(ResourcesCacheService.set(1, "push", data))
        self.assertEqual(ResourcesCacheService.get(1, "push"), data)

    def test_a_different_push_date_is_a_miss(self):
        ResourcesCacheService.set(1, "push-1", resources())

        self.assertIsNone(ResourcesCacheService.get(1, "push-2"))
        self.assertIsNone(ResourcesCacheService.get(2, "push-1"))

    def test_incomplete_resources_are_not_saved(self):
        saved = ResourcesCacheService.set(
            1,
            "push",
            resources(commits={"available": False}),
        )

        self.assertFalse(saved)
        self.assertIsNone(ResourcesCacheService.get(1, "push"))

    def test_nothing_is_saved_or_read_when_the_cache_is_disabled(self):
        ResourcesCacheService.set(1, "push", resources())

        with patch(SETTINGS, GITHUB_RESOURCES_CACHE_SECONDS="0"):
            self.assertFalse(
                ResourcesCacheService.set(2, "push", resources())
            )
            self.assertIsNone(ResourcesCacheService.get(1, "push"))

        self.assertIsNone(ResourcesCacheService.get(2, "push"))

    def test_corrupted_cache_content_is_ignored(self):
        key = ResourcesCacheService.build_key(1, "push")
        cache.set(key, {"commits": "not valid"}, 60)

        self.assertIsNone(ResourcesCacheService.get(1, "push"))

    def test_cache_errors_do_not_propagate(self):
        broken_cache = MagicMock()
        broken_cache.get.side_effect = RuntimeError("down")
        broken_cache.set.side_effect = RuntimeError("down")

        with patch(
            "api.services.resources_cache_service.cache",
            broken_cache,
        ):
            with self.assertLogs(
                "api.services.resources_cache_service",
                level="WARNING",
            ):
                self.assertIsNone(ResourcesCacheService.get(1, "push"))
                self.assertFalse(
                    ResourcesCacheService.set(1, "push", resources())
                )
