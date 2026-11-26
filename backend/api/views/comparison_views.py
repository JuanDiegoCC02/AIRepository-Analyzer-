from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.comparison_serializer import (
    RepositoryComparisonSerializer,
)
from api.services.repository_comparison_service import (
    RepositoryComparisonService,
)
from api.throttles import CompareRateThrottle


class RepositoryComparisonView(APIView):
    """
    Compares several GitHub repositories for the authenticated user.

    Every repository is analyzed (and saved in the user's history), then
    the scores are compared dimension by dimension.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [CompareRateThrottle]

    def post(self, request):
        serializer = RepositoryComparisonSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        # GitHub failures are turned into safe responses by
        # api.exceptions.api_exception_handler.
        result = RepositoryComparisonService.analyze_and_compare(
            serializer.validated_data["repository_urls"],
            user=request.user,
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
