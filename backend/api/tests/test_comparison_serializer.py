from django.test import SimpleTestCase

from api.serializers.comparison_serializer import (
    RepositoryComparisonSerializer,
)


def validate(urls):
    serializer = RepositoryComparisonSerializer(
        data={"repository_urls": urls}
    )
    serializer.is_valid()
    return serializer


class RepositoryComparisonSerializerTests(SimpleTestCase):

    def test_two_to_four_repositories_are_accepted(self):
        for count in (2, 3, 4):
            with self.subTest(count=count):
                urls = [f"https://github.com/owner/repo{i}" for i in range(count)]
                serializer = validate(urls)

                self.assertTrue(serializer.is_valid(), serializer.errors)
                self.assertEqual(
                    serializer.validated_data["repository_urls"],
                    urls,
                )

    def test_urls_are_normalized(self):
        serializer = validate(
            [
                "https://www.github.com/owner/repo",
                "https://github.com/other/project",
            ]
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["repository_urls"][0],
            "https://github.com/owner/repo",
        )

    def test_wrong_number_of_repositories_is_rejected(self):
        for urls in (
            [],
            ["https://github.com/a/one"],
            [f"https://github.com/a/r{i}" for i in range(5)],
        ):
            with self.subTest(count=len(urls)):
                self.assertFalse(validate(urls).is_valid())

    def test_missing_or_malformed_field_is_rejected(self):
        for data in (
            {},
            {"repository_urls": "https://github.com/a/one"},
            {"repository_urls": None},
            {"repository_urls": [1, 2]},
            {"repository_urls": [["x"], ["y"]]},
        ):
            with self.subTest(data=data):
                serializer = RepositoryComparisonSerializer(data=data)

                self.assertFalse(serializer.is_valid())

    def test_duplicates_are_rejected_ignoring_case(self):
        serializer = validate(
            [
                "https://github.com/Owner/Repo",
                "https://github.com/owner/repo",
            ]
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("must be different", str(serializer.errors))

    def test_invalid_urls_say_which_repository_is_wrong(self):
        serializer = validate(
            [
                "https://github.com/a/one",
                "http://github.com/a/two",
            ]
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("Repository 2:", str(serializer.errors))

    def test_other_hosts_are_rejected(self):
        serializer = validate(
            [
                "https://github.com/a/one",
                "https://gitlab.com/a/two",
            ]
        )

        self.assertFalse(serializer.is_valid())
