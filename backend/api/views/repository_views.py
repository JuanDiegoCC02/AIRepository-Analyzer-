from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from api.models.repository import Repository
from api.models.analysis import Analysis

from api.services.analyzer_service import AnalyzerService

from api.serializers.analyzer_serializer import (RepositoryAnalyzerSerializer,)
from api.serializers.repository_serializer import (RepositorySerializer,)
from api.serializers.analysis_serializer import (AnalysisSerializer,)


class RepositoryAnalyzerView(APIView):
    """
    Analyzes a GitHub repository for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

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
                repository_url,
                user=request.user,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class RepositoryListView(APIView):
    """
    Returns repositories analyzed by the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        repositories = (
            Repository.objects.filter(
                analysis__user=request.user
            )
            .distinct()
            .order_by("-updated_at")
        )

        serializer = RepositorySerializer(
            repositories,
            many=True,
        )

        return Response(
            {
                "count": repositories.count(),
                "repositories": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class RepositoryDetailView(APIView):
    """
    Returns repository metadata and the current user's analyses.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, repository_id):
        repository = get_object_or_404(
            Repository.objects.filter(
                analysis__user=request.user
            ).distinct(),
            id=repository_id,
        )

        analyses = Analysis.objects.filter(
            repository=repository,
            user=request.user,
        ).order_by("-created_at")

        repository_serializer = RepositorySerializer(
            repository,
        )

        analysis_serializer = AnalysisSerializer(
            analyses,
            many=True,
        )

        return Response(
            {
                "repository": repository_serializer.data,
                "analyses_count": analyses.count(),
                "analyses": analysis_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class RepositoryHistoryView(APIView):
    """
    Returns only the authenticated user's analysis history.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, repository_id):
        repository = get_object_or_404(
            Repository.objects.filter(
                analysis__user=request.user
            ).distinct(),
            id=repository_id,
        )

        analyses = Analysis.objects.filter(
            repository=repository,
            user=request.user,
        ).order_by("-created_at")

        serializer = AnalysisSerializer(
            analyses,
            many=True,
        )

        return Response(
            {
                "repository": repository.full_name,
                "repository_id": repository.id,
                "count": analyses.count(),
                "history": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
