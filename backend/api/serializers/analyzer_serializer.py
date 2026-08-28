from rest_framework import serializers


class RepositoryAnalyzerSerializer(serializers.Serializer):

    repository_url = serializers.URLField(
        required=True,
        allow_blank=True,
    )

    def validate_repository_url(self, value):

        value = value.strip()

        if "github.com/" not in value:
            raise serializers.ValidationError(
                "The URL must belong to GitHub."
            )

        if value.endswith("/"):
            vlaue = value.rstrip("/")

        parts = value.split("/")

        if len(parts) < 2:
            raise serializers.ValidationError(
                "Invalid GitHub repository URL."
            )

        owner = parts[-2]

        repository = parts[-1]

        if not owner or not repository:
            raise serializers.ValidationError(
                "GitHub owner and repository are required."
            )

        return value