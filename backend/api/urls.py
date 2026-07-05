from django.urls import path 
from api.views import RepositoryAnalyzerView

urlpatterns = [

    path("repositories/analyze/",
         RepositoryAnalyzerView.as_view(),
         name = "repository-analyze"
         ),

]