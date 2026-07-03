from django.contrib import admin
from .models import Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "language",
        "stars",
        "forks",
        "created_at",
    )

    search_fields = (
        "name",
        "owner",
        "language",
    )

    list_filter = (
        "language",
    )

    ordering = (
        "-stars",
    )