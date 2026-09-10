from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.models.repository import Repository
from api.models.analysis import Analysis

from api.services.analyzer_service import AnalyzerService

from api.serializers.analyzer_serializer import (RepositoryAnalyzerSerializer)
from api.serializers.repository_serializer import (RepositorySerializer)
from api.serializers.analysis_serializer import (AnalysisSerializer)


class RepositoryAnalyzerView(APIView):
    """
    API endpoint responsible for analyzing a GitHub repository.
    """

    def post(self, request):

        serializer = RepositoryAnalyzerSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        repository_url = serializer.validated_data[
            "repository_url"
        ]

        try:

            result = AnalyzerService.analyze_repository(
                repository_url
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
                    "error": "Repository analysis failed.",
                    "details": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


class RepositoryListView(APIView):
    """
    Returns all repositories analyzed and stored in the database.
    """

    def get(self, request):

        repositories = Repository.objects.all().order_by(
            "-updated_at"
        )

        serializer = RepositorySerializer(
            repositories,
            many=True
        )

        return Response(
            {
                "count": repositories.count(),
                "repositories": serializer.data
            },
            status=status.HTTP_200_OK
        )


class RepositoryDetailView(APIView):
    """
    Returns detailed information about a stored repository.
    """

    def get(self, request, repository_id):

        try:

            repository = Repository.objects.get(
                id=repository_id
            )

        except Repository.DoesNotExist:

            return Response(
                {
                    "error": "Repository not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        repository_serializer = RepositorySerializer(
            repository
        )

        analyses = Analysis.objects.filter(
            repository=repository
        ).order_by("-created_at")

        analysis_serializer = AnalysisSerializer(
            analyses,
            many=True
        )

        return Response(
            {
                "repository": repository_serializer.data,
                "analyses_count": analyses.count(),
                "analyses": analysis_serializer.data
            },
            status=status.HTTP_200_OK
        )


class RepositoryHistoryView(APIView):
    """
    Returns the analysis history of a repository.
    """

    def get(self, request, repository_id):

        try:

            repository = Repository.objects.get(
                id=repository_id
            )

        except Repository.DoesNotExist:

            return Response(
                {
                    "error": "Repository not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        analyses = Analysis.objects.filter(
            repository=repository
        ).order_by("-created_at")

        serializer = AnalysisSerializer(
            analyses,
            many=True
        )

        return Response(
            {
                "repository": repository.full_name,
                "repository_id": repository.id,
                "count": analyses.count(),
                "history": serializer.data
            },
            status=status.HTTP_200_OK
        )