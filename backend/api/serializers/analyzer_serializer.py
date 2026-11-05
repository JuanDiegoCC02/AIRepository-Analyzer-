from urllib.parse import urlparse

from rest_framework import serializers


class RepositoryAnalyzerSerializer(serializers.Serializer):

    repository_url = serializers.URLField(
        required=True,
        allow_blank=False,
        max_length=500,
    )

    def validate_repository_url(self, value):

        value = value.strip()
        parsed_url = urlparse(value)

        # Only HTTPS is allowed.
        if parsed_url.scheme.lower() != "https":
            raise serializers.ValidationError(
                "The repository URL must use HTTPS."
            )

        # Only GitHub domains are allowed.
        hostname = parsed_url.hostname

        if not hostname or hostname.lower() not in {
            "github.com",
            "www.github.com",
        }:
            raise serializers.ValidationError(
                "The URL must belong to GitHub."
            )

        # Credentials are not allowed.
        if parsed_url.username or parsed_url.password:
            raise serializers.ValidationError(
                "Credentials are not allowed in the repository URL."
            )

        # Only standard HTTPS port is allowed.
        try:
            port = parsed_url.port
        except ValueError:
            raise serializers.ValidationError(
                "The repository URL contains an invalid port."
            )

        if port not in (None, 443):
            raise serializers.ValidationError(
                "The repository URL must use the standard HTTPS port."
            )

        # Query parameters and fragments are not allowed.
        if parsed_url.query or parsed_url.fragment:
            raise serializers.ValidationError(
                "The GitHub repository URL cannot contain "
                "query parameters or fragments."
            )

        path = parsed_url.path.strip("/")
        parts = path.split("/")

        # Exactly owner/repository.
        if len(parts) != 2:
            raise serializers.ValidationError(
                "The URL must contain a GitHub owner and repository."
            )

        owner, repository = parts

        if not owner or not repository:
            raise serializers.ValidationError(
                "GitHub owner and repository are required."
            )

        if "%" in path or "\\" in path:
            raise serializers.ValidationError(
                "The repository URL contains an invalid path."
            )

        if owner in {".", ".."} or repository in {".", ".."}:
            raise serializers.ValidationError(
                "The repository URL contains an invalid path."
            )

        return f"https://github.com/{owner}/{repository}"