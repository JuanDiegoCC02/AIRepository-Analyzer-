from django.db import models
from django.conf import settings
from .repository import Repository

class Analysis(models.Model):

    LEGACY_SCORE_VERSION = 1
    CURRENT_SCORE_VERSION = 3

    repository = models.ForeignKey(

        Repository,
        on_delete=models.CASCADE,
        related_name="analysis"
        )
    
    project_type = models.CharField(max_length=100)

    popularity_score = models.PositiveSmallIntegerField(default=0)

    activity_score = models.PositiveSmallIntegerField(default=0)

    documentation_score = models.PositiveSmallIntegerField(default=0)

    maintainability_score = models.PositiveSmallIntegerField(default=0)

    code_quality_score = models.PositiveSmallIntegerField(default=0)

    community_score = models.PositiveSmallIntegerField(default=0)

    overall_score = models.PositiveSmallIntegerField(default=0)

    score_version = models.PositiveSmallIntegerField(default=LEGACY_SCORE_VERSION,)

    ai_summary = models.TextField(blank=True, null=True)

    recommendations = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analyses",
        null=True,
        blank=True,
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

    def __str__(self):
        
        return (
            f"{self.repository.full_name}"
            f"Analysis - {self.created_at}"
        )
    