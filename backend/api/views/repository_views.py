from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.services.analyzer_service import AnalyzerService


class RepositoryAnalyzerView(APIView):

    """
    API endpoint respomsible for analyzing a GitHub repository.
    """

    def post(self, request):

        repository_url = request.data.get("repository_url")

        if not repository_url:
            return Response(
                {"error": "repository URL is required. "},
                status = status.HTTP_400_BAD_REQUEST    
            ) 

        if not isinstance(repository_url, str):
            return Response(
                {
                    "error": "repository URL must be a string."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        repository_url = repository_url.strip()

        if not repository_url:
            return Response(
                {
                    "error": "repository URL cannot be empty."
                },
            )
        
        try:
            result = AnalyzerService.analyze_repository(repository_url)

            return Response(
                result,
                status=status.HTTP_200_OK
            )

        except ValueError as error:
            return Response(
                {
                    "error": str(error)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as error:
            return Response(
                {
                    "error": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
      

