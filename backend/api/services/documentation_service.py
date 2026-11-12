import math
from urllib.parse import urlparse


class DocumentationService:
    """
    Scores how well a repository is documented, from 0 to 100.

    The README is the most important piece of documentation, so it carries
    55% of the score. Metadata that helps people understand and reuse the
    project (description, docs site, license, topics) carries the rest.

    Signals (maximum points):
      - readme_length:    words in the README                   (30)
      - readme_structure: number of headings in the README      (25)
      - description:      short description of the repository   (10)
      - docs_site:        homepage, GitHub Pages or wiki        (15)
      - license:          the project declares a license        (10)
      - topics:           topics that make it discoverable      (10)

    If the README information is not provided at all (None), its two
    signals are left out and the result is rescaled. If it is provided
    and the repository has no README, they earn 0 points: not having a
    README is a real documentation problem.
    """

    README_LENGTH_MAX = 30
    README_STRUCTURE_MAX = 25
    DESCRIPTION_MAX = 10
    DOCS_SITE_MAX = 15
    LICENSE_MAX = 10
    TOPICS_MAX = 10

    # 300 words (or more) earn the full README length points.
    WORDS_FOR_FULL_SCORE = 300

    # 6 headings (or more) earn the full README structure points.
    SECTIONS_FOR_FULL_SCORE = 6

    DESCRIPTION_FULL_LENGTH = 50

    @staticmethod
    def _non_negative_int(value):
        """Coerce untrusted numeric input into an integer >= 0."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0

        if isinstance(value, float) and not math.isfinite(value):
            return 0

        return max(0, int(value))

    @staticmethod
    def _is_web_address(value):
        """True when the value looks like an http(s) address."""
        if not isinstance(value, str) or not value.strip():
            return False

        parsed = urlparse(value.strip())

        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @classmethod
    def _readme_points(cls, readme):
        """Return (length_points, structure_points), or (None, None)."""
        if not isinstance(readme, dict):
            return None, None

        if readme.get("exists") is not True:
            return 0.0, 0.0

        words = cls._non_negative_int(readme.get("word_count"))
        sections = cls._non_negative_int(readme.get("sections"))

        length_points = cls.README_LENGTH_MAX * min(
            1.0,
            words / cls.WORDS_FOR_FULL_SCORE,
        )

        structure_points = cls.README_STRUCTURE_MAX * min(
            1.0,
            sections / cls.SECTIONS_FOR_FULL_SCORE,
        )

        return length_points, structure_points

    @classmethod
    def _description_points(cls, repository):
        description = repository.get("description")

        if not isinstance(description, str) or not description.strip():
            return 0.0

        if len(description.strip()) >= cls.DESCRIPTION_FULL_LENGTH:
            return float(cls.DESCRIPTION_MAX)

        return cls.DESCRIPTION_MAX / 2

    @classmethod
    def _docs_site_points(cls, repository):
        has_docs_site = (
            cls._is_web_address(repository.get("homepage"))
            or repository.get("has_pages") is True
            or repository.get("has_wiki") is True
        )

        return float(cls.DOCS_SITE_MAX) if has_docs_site else 0.0

    @classmethod
    def _license_points(cls, repository):
        license_data = repository.get("license")

        has_license = isinstance(license_data, dict) and bool(
            license_data.get("name") or license_data.get("spdx_id")
        )

        return float(cls.LICENSE_MAX) if has_license else 0.0

    @classmethod
    def _topics_points(cls, repository):
        topics = repository.get("topics")

        if not isinstance(topics, list):
            return 0.0

        count = len(
            [
                topic
                for topic in topics
                if isinstance(topic, str) and topic.strip()
            ]
        )

        if count >= 5:
            return float(cls.TOPICS_MAX)

        if count >= 2:
            return cls.TOPICS_MAX * 0.6

        if count == 1:
            return cls.TOPICS_MAX * 0.3

        return 0.0

    @classmethod
    def breakdown(cls, repository, readme=None):
        """
        Points earned by every signal.

        'points' is None when the signal has no data. This makes the
        score explainable (and useful as input for the AI summary later).
        """
        if not isinstance(repository, dict):
            repository = {}

        length_points, structure_points = cls._readme_points(readme)

        raw = {
            "readme_length": (length_points, cls.README_LENGTH_MAX),
            "readme_structure": (
                structure_points,
                cls.README_STRUCTURE_MAX,
            ),
            "description": (
                cls._description_points(repository),
                cls.DESCRIPTION_MAX,
            ),
            "docs_site": (
                cls._docs_site_points(repository),
                cls.DOCS_SITE_MAX,
            ),
            "license": (
                cls._license_points(repository),
                cls.LICENSE_MAX,
            ),
            "topics": (
                cls._topics_points(repository),
                cls.TOPICS_MAX,
            ),
        }

        return {
            name: {
                "points": None if points is None else round(points, 2),
                "max": maximum,
            }
            for name, (points, maximum) in raw.items()
        }

    @classmethod
    def calculate(cls, repository, readme=None):
        """
        Return the documentation score (integer from 0 to 100).

        'readme' is the dictionary produced by ReadmeService.analyze().
        It is optional, so calculate(github_repository) keeps working.
        """
        if not isinstance(repository, dict):
            return 0

        signals = cls.breakdown(repository, readme=readme)

        earned = 0.0
        possible = 0

        for signal in signals.values():
            if signal["points"] is None:
                continue

            earned += signal["points"]
            possible += signal["max"]

        if possible == 0:
            return 0

        return max(0, min(100, round(earned / possible * 100)))