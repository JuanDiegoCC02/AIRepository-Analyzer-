import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ResourcesCacheService:
    """
    Keeps the data collected from GitHub for a short time.

    When the same repository is analyzed again and nothing was pushed to
    it, the saved data is reused and only the repository request is made.

    Only complete results are saved. If a request failed, the next
    analysis must try again instead of repeating missing data.
    """

    KEY_PREFIX = "github-resources:v1"
    DEFAULT_TTL = 900
    MAX_TTL = 86400

    # Resources that report whether GitHub could provide them.
    REQUIRED_AVAILABLE = ("commits", "structure", "readme")

    # Every resource that must be present in a saved result.
    REQUIRED_KEYS = (
        "technologies",
        "readme",
        "contributors",
        "releases",
        "commits",
        "structure",
    )

    @classmethod
    def ttl(cls):
        """Return the time to live in seconds (0 means disabled)."""
        value = getattr(
            settings,
            "GITHUB_RESOURCES_CACHE_SECONDS",
            cls.DEFAULT_TTL,
        )

        if isinstance(value, bool):
            return cls.DEFAULT_TTL

        try:
            seconds = int(value)
        except (TypeError, ValueError):
            return cls.DEFAULT_TTL

        return max(0, min(seconds, cls.MAX_TTL))

    @classmethod
    def build_key(cls, github_id, pushed_at):
        """
        Build the cache key, or None when the repository has no valid id.
        """
        if (
            isinstance(github_id, bool)
            or not isinstance(github_id, int)
            or github_id <= 0
        ):
            return None

        digest = hashlib.sha256(
            str(pushed_at).encode("utf-8")
        ).hexdigest()[:16]

        return f"{cls.KEY_PREFIX}:{github_id}:{digest}"

    @classmethod
    def is_complete(cls, resources):
        """True when every resource is present and could be retrieved."""
        if not isinstance(resources, dict):
            return False

        if any(key not in resources for key in cls.REQUIRED_KEYS):
            return False

        for name in cls.REQUIRED_AVAILABLE:
            data = resources[name]

            if not isinstance(data, dict) or data.get("available") is not True:
                return False

        return True

    @classmethod
    def get(cls, github_id, pushed_at):
        """Return the saved resources, or None when there are none."""
        if cls.ttl() == 0:
            return None

        key = cls.build_key(github_id, pushed_at)

        if key is None:
            return None

        try:
            resources = cache.get(key)
        except Exception:
            # A broken cache must never break an analysis.
            logger.warning("The resources cache could not be read.")
            return None

        if not cls.is_complete(resources):
            return None

        return resources

    @classmethod
    def set(cls, github_id, pushed_at, resources):
        """Save complete resources. Returns True when they were saved."""
        ttl = cls.ttl()

        if ttl == 0 or not cls.is_complete(resources):
            return False

        key = cls.build_key(github_id, pushed_at)

        if key is None:
            return False

        try:
            cache.set(key, resources, ttl)
        except Exception:
            logger.warning("The resources cache could not be written.")
            return False

        return True
