from django.db import models


class Repository(models.Model):
    github_id = models.BigIntegerField(unique=True)

    owner = models.CharField(max_length=250)

    name = models.CharField(max_length=250)

    full_name= models.CharField(max_length=280)

    description = models.TextField(blank=True, null= True)

    topics = models.JSONField(default=list)

    html_url = models.URLField(max_length=500)

    language = models.CharField(max_length=200, blank=True, null=True)

    license_name = models.CharField(max_length=200, blank=True, null=True)

    default_branch = models.CharField(max_length=200, blank=True, null=True)

    stars = models.PositiveIntegerField(default=0)

    forks = models.PositiveIntegerField(default=0)

    watchers = models.PositiveIntegerField(default=0)

    open_issues = models.PositiveIntegerField(default=0)

    github_created_at = models.DateTimeField()

    github_updated_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "repositories"

        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["name"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return self.full_name


