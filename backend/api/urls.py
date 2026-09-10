from django.urls import path

from api.views.repository_views import (
    RepositoryAnalyzerView,
    RepositoryListView,
    RepositoryDetailView,
    RepositoryHistoryView,
)


urlpatterns = [
     path(
          "analyze/",
          RepositoryAnalyzerView.as_view(),
          name="repository-analyze"
     ),

     path(
          "repositories/",
          RepositoryListView.as_view(),
          name="repository-list"
     ),

     path(
          "repositories/<int:repository_id>/",
          RepositoryDetailView.as_view(),
          name="repository-detail"
     ),

     path(
          "repositories/<int:repository_id>/history/",
          RepositoryHistoryView.as_view(),
          name="repository-history"
     ),

]