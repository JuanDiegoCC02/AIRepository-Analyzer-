from urllib.parse import urlparse
from rest_framework import serializers


class RepositoryAnalyzerSerializer(serializers.Serializer):

    repository_url = serializers.URLField(
        required=True,
        allow_blank=True,
    )

    def validate_repository_url(self, value):

        value = value.strip()

        parsed_url = urlparse(value)


        if parsed_url.scheme !=  "https":
            raise serializers.ValidationError(
                "The URL must belong to GitHub."
            )

        if parsed_url.netloc.lower() not in {
            "github.com",
            "www.github.com",
        }:
            raise serializers.ValidationError(
                "The URL must belong to GitHub."
            )

        if parsed_url.query or parsed_url.fragment:
            raise serializers.ValidationError(
                "The GitHub repository URL cannot contain query parameters or framents."
            )


        path = parsed_url.path.strip("/")

        parts = path.split("/")


        if len (parts) != 2:
            raise serializers.ValidationError(
                "The URL must contain a GitHub owner and repository."
            )

        owner, repository = parts


        if not owner or not repository:
            raise serializers.ValidationError(
                "GitHub owner and repository are required."
            )

        return f'https://github.com{owner}/{repository}'