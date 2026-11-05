from rest_framework import serializers

from api.models.repository import Repository


class RepositorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Repository
        fields = [
            "id",
            "github_id",
            "owner",
            "name",
            "full_name",
            "description",
            "topics",
            "html_url",
            "language",
            "license_name",
            "default_branch",
            "stars",
            "forks",
            "watchers",
            "open_issues",
            "github_created_at",
            "github_updated_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields