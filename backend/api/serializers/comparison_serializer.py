from rest_framework import serializers

from api.serializers.analyzer_serializer import validate_github_repository_url


class RepositoryComparisonSerializer(serializers.Serializer):
    """
    Validates the repositories to compare.

    Between MIN_REPOSITORIES and MAX_REPOSITORIES different GitHub
    repositories. Every analysis costs GitHub requests, so the maximum
    protects the shared GitHub quota.
    """

    MIN_REPOSITORIES = 2
    MAX_REPOSITORIES = 4

    repository_urls = serializers.ListField(
        child=serializers.URLField(max_length=500),
        allow_empty=False,
        min_length=MIN_REPOSITORIES,
        max_length=MAX_REPOSITORIES,
    )

    def validate_repository_urls(self, value):
        urls = []
        seen = set()

        for position, url in enumerate(value, start=1):
            try:
                normalized = validate_github_repository_url(url)
            except serializers.ValidationError as error:
                raise serializers.ValidationError(
                    f"Repository {position}: {error.detail[0]}"
                )

            # GitHub names are not case sensitive.
            key = normalized.lower()

            if key in seen:
                raise serializers.ValidationError(
                    "The repositories to compare must be different."
                )

            seen.add(key)
            urls.append(normalized)

        return urls
