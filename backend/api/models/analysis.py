from django.db import models

from .repository import Repository

class Analysis(models.Model):

    repository = models.OneToOneField(
        Repository,
        on_delete=models.CASCADE,
        related_name="analysis"
        )
    
    project_type = models.CharField(max_length=100)

    popularity_score = models.PositiveSmallIntegerField(default=0)

    activity_score = models.PositiveSmallIntegerField(default=0)

    documentation_score = models.PositiveSmallIntegerField(default=0)

    maintainability_score = models.PositiveSmallIntegerField(default=0)

    overall_score = models.PositiveSmallIntegerField(default=0)

    ai_summary = models.TextField(blank=True)

    recommendations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analysis"

    def __str__(self):
        return f"Analysis - {self.repository.full_name}"
    