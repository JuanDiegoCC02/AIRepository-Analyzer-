from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from api.serializers.analyzer_serializer import (RepositoryAnalyzerSerializer, )

class RepositoryAnalyzerSerializerTests(SimpleTestCase):

    def test_valid_github_repository_url(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                 "https://github.com/facebook/react"
                )
            }
        )

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )


    def test_valid_github_repository_url_with_trailing_slash(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://github.com/facebook/react/"
                )
            }
        )

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )


    def test_www_github_repository_url(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://www.github.com/facebook/react"
                )
            }
        )

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validated_data["repository_url"],
            "https://github.com/facebook/react",
        )


    def test_http_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "http://github.com/facebook/react"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_external_domain_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://example.com/facebook/react"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_fake_github_domain_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://evil.com/github.com/facebook/react"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_query_parameter_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://github.com/facebook/react?test=123"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_fragment_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://github.com/facebook/react#readme"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_missing_repository_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://github.com/facebook"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_extra_path_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": (
                    "https://github.com/facebook/react/issues"
                )
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_empty_url_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={
                "repository_url": ""
            }
        )

        self.assertFalse(serializer.is_valid())


    def test_missing_url_is_rejected(self):
        serializer = RepositoryAnalyzerSerializer(
            data={}
        )

        self.assertFalse(serializer.is_valid())
        