from urllib.parse import urlparse

from rest_framework import serializers


class RepositoryAnalyzerSerializer(serializers.Serializer):

    repository_url = serializers.URLField(
        required=True,
        allow_blank=False,
    )

    def validate_repository_url(self, value):

        value = value.strip()

        parsed_url = urlparse(value)

        # Only HTTPS is allowed.
        if parsed_url.scheme != "https":
            raise serializers.ValidationError(
                "The repository URL must use HTTPS."
            )

        # Only GitHub domains are allowed.
        hostname = parsed_url.hostname

        if hostname is None or hostname.lower() not in {
            "github.com",
            "www.github.com",
        }:
            raise serializers.ValidationError(
                "The URL must belong to GitHub."
            )

        # Query parameters and fragments are not allowed.
        if parsed_url.query or parsed_url.fragment:
            raise serializers.ValidationError(
                "The GitHub repository URL cannot contain "
                "query parameters or fragments."
            )

        path = parsed_url.path.strip("/")

        parts = path.split("/")

        # A repository URL must contain exactly:
        # /owner/repository
        if len(parts) != 2:
            raise serializers.ValidationError(
                "The URL must contain a GitHub owner and repository."
            )

        owner, repository = parts

        if not owner or not repository:
            raise serializers.ValidationError(
                "GitHub owner and repository are required."
            )

        return f"https://github.com/{owner}/{repository}"