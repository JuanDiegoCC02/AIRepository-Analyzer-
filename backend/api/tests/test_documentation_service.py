from django.test import SimpleTestCase

from api.services.documentation_service import DocumentationService


def readme(words=300, sections=6, exists=True):
    return {
        "exists": exists,
        "size": words * 6,
        "word_count": words,
        "sections": sections,
    }


FULL_REPOSITORY = {
    "description": (
        "A complete description that explains what this project does "
        "and who it is for."
    ),
    "homepage": "https://docs.example.org",
    "license": {"name": "MIT License", "spdx_id": "MIT"},
    "topics": ["python", "web", "api", "backend", "framework"],
}


class DocumentationServiceTests(SimpleTestCase):

    def test_fully_documented_repository_scores_100(self):
        score = DocumentationService.calculate(
            FULL_REPOSITORY,
            readme=readme(),
        )

        self.assertEqual(score, 100)

    def test_flask_like_repository_scores_high_with_its_readme(self):
        # Real data from pallets/flask: 208 words, 5 headings, 57 character
        # description, docs site, license and 7 topics. The old formula
        # ignored the README and rated this 70.
        score = DocumentationService.calculate(
            {
                "description": (
                    "The Python micro framework for building web "
                    "applications."
                ),
                "homepage": "https://flask.palletsprojects.com",
                "license": {"name": "BSD 3-Clause"},
                "topics": ["flask", "jinja", "pallets", "python",
                           "web-framework", "werkzeug", "wsgi"],
            },
            readme=readme(words=208, sections=5),
        )

        self.assertGreaterEqual(score, 80)
        self.assertLessEqual(score, 95)

    def test_repository_without_readme_loses_the_readme_points(self):
        with_readme = DocumentationService.calculate(
            FULL_REPOSITORY,
            readme=readme(),
        )
        without_readme = DocumentationService.calculate(
            FULL_REPOSITORY,
            readme=readme(words=0, sections=0, exists=False),
        )

        self.assertEqual(with_readme - without_readme, 55)

    def test_unknown_readme_information_rescales_instead_of_penalizing(self):
        score = DocumentationService.calculate(FULL_REPOSITORY)
        breakdown = DocumentationService.breakdown(FULL_REPOSITORY)

        self.assertEqual(score, 100)
        self.assertIsNone(breakdown["readme_length"]["points"])
        self.assertIsNone(breakdown["readme_structure"]["points"])

    def test_longer_readme_never_lowers_the_score(self):
        previous = -1

        for words in range(0, 600, 10):
            score = DocumentationService.calculate(
                FULL_REPOSITORY,
                readme=readme(words=words),
            )

            self.assertGreaterEqual(score, previous)
            previous = score

    def test_more_headings_never_lower_the_score(self):
        previous = -1

        for sections in range(0, 12):
            score = DocumentationService.calculate(
                FULL_REPOSITORY,
                readme=readme(sections=sections),
            )

            self.assertGreaterEqual(score, previous)
            previous = score

    def test_stars_and_activity_do_not_affect_documentation(self):
        base = DocumentationService.calculate(
            FULL_REPOSITORY,
            readme=readme(),
        )
        popular = DocumentationService.calculate(
            {
                **FULL_REPOSITORY,
                "stargazers_count": 900000,
                "forks_count": 50000,
                "open_issues_count": 0,
                "has_issues": True,
                "has_projects": True,
                "has_discussions": True,
            },
            readme=readme(),
        )

        self.assertEqual(base, popular)

    def test_docs_site_accepts_homepage_pages_or_wiki(self):
        for field, value in (
            ("homepage", "https://docs.example.org"),
            ("has_pages", True),
            ("has_wiki", True),
        ):
            with self.subTest(field=field):
                breakdown = DocumentationService.breakdown(
                    {field: value},
                    readme=readme(),
                )

                self.assertEqual(breakdown["docs_site"]["points"], 15)

    def test_homepage_must_be_a_web_address(self):
        for bad_homepage in ("", "   ", "not a url", "javascript:alert(1)",
                             "ftp://example.org", None, 123):
            with self.subTest(homepage=bad_homepage):
                breakdown = DocumentationService.breakdown(
                    {"homepage": bad_homepage},
                    readme=readme(),
                )

                self.assertEqual(breakdown["docs_site"]["points"], 0)

    def test_short_description_earns_half_the_points(self):
        short = DocumentationService.breakdown(
            {"description": "Short text"},
            readme=readme(),
        )
        long = DocumentationService.breakdown(
            {"description": "x" * 60},
            readme=readme(),
        )
        empty = DocumentationService.breakdown(
            {"description": "   "},
            readme=readme(),
        )

        self.assertEqual(short["description"]["points"], 5)
        self.assertEqual(long["description"]["points"], 10)
        self.assertEqual(empty["description"]["points"], 0)

    def test_topics_are_scored_by_count(self):
        expected = {0: 0, 1: 3, 2: 6, 4: 6, 5: 10, 9: 10}

        for count, points in expected.items():
            with self.subTest(topics=count):
                breakdown = DocumentationService.breakdown(
                    {"topics": [f"topic{i}" for i in range(count)]},
                    readme=readme(),
                )

                self.assertEqual(breakdown["topics"]["points"], points)

    def test_license_requires_a_name_or_identifier(self):
        with_license = DocumentationService.breakdown(
            {"license": {"name": "MIT License"}},
            readme=readme(),
        )
        without_license = DocumentationService.breakdown(
            {"license": None},
            readme=readme(),
        )
        empty_license = DocumentationService.breakdown(
            {"license": {}},
            readme=readme(),
        )

        self.assertEqual(with_license["license"]["points"], 10)
        self.assertEqual(without_license["license"]["points"], 0)
        self.assertEqual(empty_license["license"]["points"], 0)

    def test_invalid_inputs_return_zero_without_crashing(self):
        self.assertEqual(DocumentationService.calculate(None), 0)
        self.assertEqual(DocumentationService.calculate("text"), 0)
        self.assertEqual(
            DocumentationService.calculate({}, readme=readme(exists=False)),
            0,
        )

    def test_untrusted_readme_numbers_do_not_crash_or_inflate(self):
        for bad_value in ("many", None, True, float("inf"),
                          float("nan"), -5):
            with self.subTest(value=bad_value):
                score = DocumentationService.calculate(
                    FULL_REPOSITORY,
                    readme={
                        "exists": True,
                        "word_count": bad_value,
                        "sections": bad_value,
                    },
                )

                self.assertIsInstance(score, int)
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 100)

    def test_malformed_repository_fields_do_not_crash(self):
        score = DocumentationService.calculate(
            {
                "description": 123,
                "homepage": ["x"],
                "license": "MIT",
                "topics": "python",
            },
            readme=readme(),
        )

        self.assertIsInstance(score, int)
        self.assertLessEqual(score, 100)