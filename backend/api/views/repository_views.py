from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.services import GitHubService


class RepositoryAnalyzerView(APIView):

    def post(self, request):

        repository_url = request.data.get("url")

        if not repository_url:
            return Response(
                {"error": "Repository URL is required. "},
                status = status.HTTP_400_BAD_REQUEST    
            ) 
        
        try:
            
            repository_data = GitHubService.get_repository(repository_url)

            return Response(repository_data)
        
        except Exception as e: 

            return Response(
                {"error": str(e)},
                status = status.HTTP_400_BAD_REQUEST    
            )
