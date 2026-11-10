from django.test import SimpleTestCase

from api.serializers.analyzer_serializer import RepositoryAnalyzerSerializer


class RepositoryAnalyzerSerializerTests(SimpleTestCase):

    def validate(self, url):
        serializer = RepositoryAnalyzerSerializer(
            data={"repository_url": url}
        )
        return serializer, serializer.is_valid()

    # ---- Valid URLs ----

    def test_valid_github_repository_url(self):
        serializer, is_valid = self.validate(
            "https://github.com/facebook/react"
        )

        self.assertTrue(is_valid)
        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )

    def test_trailing_slash_is_normalized(self):
        serializer, is_valid = self.validate(
            "https://github.com/facebook/react/"
        )

        self.assertTrue(is_valid)
        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )

    def test_www_domain_is_normalized(self):
        serializer, is_valid = self.validate(
            "https://www.github.com/facebook/react"
        )

        self.assertTrue(is_valid)
        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )

    # ---- Scheme and domain ----

    def test_rejects_http_url(self):
        _, is_valid = self.validate("http://github.com/facebook/react")
        self.assertFalse(is_valid)

    def test_rejects_non_github_domain(self):
        _, is_valid = self.validate("https://gitlab.com/user/project")
        self.assertFalse(is_valid)

    def test_rejects_unrelated_external_domain(self):
        _, is_valid = self.validate("https://example.com/facebook/react")
        self.assertFalse(is_valid)

    def test_rejects_fake_github_domain_in_path(self):
        _, is_valid = self.validate(
            "https://evil.com/github.com/facebook/react"
        )
        self.assertFalse(is_valid)

    # ---- Credentials, port, query and fragment ----

    def test_rejects_url_with_credentials(self):
        _, is_valid = self.validate(
            "https://user:password@github.com/facebook/react"
        )
        self.assertFalse(is_valid)

    def test_rejects_non_standard_port(self):
        _, is_valid = self.validate(
            "https://github.com:8443/facebook/react"
        )
        self.assertFalse(is_valid)

    def test_rejects_url_with_query_parameters(self):
        _, is_valid = self.validate(
            "https://github.com/facebook/react?tab=readme"
        )
        self.assertFalse(is_valid)

    def test_rejects_url_with_fragment(self):
        _, is_valid = self.validate(
            "https://github.com/facebook/react#readme"
        )
        self.assertFalse(is_valid)

    # ---- Path ----

    def test_rejects_missing_repository(self):
        _, is_valid = self.validate("https://github.com/facebook")
        self.assertFalse(is_valid)

    def test_rejects_extra_path(self):
        _, is_valid = self.validate(
            "https://github.com/facebook/react/issues"
        )
        self.assertFalse(is_valid)

    def test_rejects_repository_url_with_branch_path(self):
        _, is_valid = self.validate(
            "https://github.com/facebook/react/tree/main"
        )
        self.assertFalse(is_valid)

    def test_rejects_encoded_slash_in_path(self):
        _, is_valid = self.validate("https://github.com/facebook%2Freact")
        self.assertFalse(is_valid)

    def test_rejects_percent_encoded_characters_in_path(self):
        _, is_valid = self.validate(
            "https://github.com/face%62ook/react"
        )
        self.assertFalse(is_valid)

    # ---- Empty input ----

    def test_rejects_empty_repository_url(self):
        _, is_valid = self.validate("")
        self.assertFalse(is_valid)

    def test_rejects_missing_repository_url_field(self):
        serializer = RepositoryAnalyzerSerializer(data={})
        self.assertFalse(serializer.is_valid())