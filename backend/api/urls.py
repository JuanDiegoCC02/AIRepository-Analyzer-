from django.urls import path 
from api.views import RepositoryAnalyzerView, RepositoryListView, 

urlpatterns = [

    path("repositories/analyze/",
         RepositoryAnalyzerView.as_view(),
         name = "repository-analyze"
         ),

    path("repositories/",
         RepositoryListView.as_view(),
         name = "repository-list"
         ),

    path("repostories/<int:pk>/",
         RepositoryDetailView.as_view(),
         name = "repository-detail"
         ),

]