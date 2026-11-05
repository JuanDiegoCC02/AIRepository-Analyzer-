from django.test import SimpleTestCase
from api.serializers.analyzer_serializer import RepositoryAnalyzerSerializer


class RepositoryAnalyzerSerializerTests(SimpleTestCase):

    def test_valid_github_repository_url(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://github.com/facebook/react"
            }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )

    def test_rejects_http_url(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "http://github.com/facebook/react"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_non_github_domain(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://gitlab.com/user/project"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_repository_url_with_extra_path(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://github.com/facebook/react/tree/main"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_url_with_query_parameters(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://github.com/facebook/react?tab=readme"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_url_with_credentials(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://user:password@github.com/facebook/react"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_non_standard_port(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://github.com:8443/facebook/react"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_encoded_path(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": "https://github.com/facebook%2Freact"
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_rejects_empty_repository_url(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": ""
            }
        )

        self.assertFalse(serializer.is_valid())