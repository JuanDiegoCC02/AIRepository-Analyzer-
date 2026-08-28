from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.services.analyzer_service import AnalyzerService

from api.serializers.analyzer_serializer import RepositoryAnalyzerSerializer


class RepositoryAnalyzerView(APIView):

    """
    API endpoint respomsible for analyzing a GitHub repository.
    """

    def post(self, request):

        serializer = RepositoryAnalyzerSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        repository_url = serializer.validated_data["repository_url"]


        try:
            result = AnalyzerService.analyze_repository(repository_url)

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
                    "error": "Repository analysis falled.",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            result, 
            status=status.HTTP_200_OK,
        )

           
class RepositoryListView(APIView):

    def get(self, request):

        return Response(
            {
                "message": "Repository list endpoint."
            },
            status=status.HTTP_200_OK
        )


class RepositoryDetailView(APIView):

    def get(self, request, repository_id):

        return Response(
            {
                "message": "Repository detail endpoint.",
                "repository_id": repository_id
            },
            status=status.HTTP_200_OK
        )

