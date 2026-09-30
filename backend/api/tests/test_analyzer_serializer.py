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

        