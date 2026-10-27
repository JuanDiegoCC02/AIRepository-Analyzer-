from rest_framework import serializers

from api.models.analysis import Analysis


class AnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Analysis

        fields = [
            "id",
            "repository",
            "project_type",
            "popularity_score",
            "activity_score",
            "documentation_score",
            "maintainability_score",
            "code_quality_score",
            "community_score",
            "overall_score",
            "ai_summary",
            "recommendations",
            "created_at",
        ]

        read_only_fields = fields
