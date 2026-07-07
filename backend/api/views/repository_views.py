from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.services import AnalyzerService
from rest_framework.generics import ListAPIView, RetrieveAPIView
from api.models import Repository
from api.serializers import RepositorySerializer



class RepositoryAnalyzerView(APIView):

    def post(self, request):

        repository_url = request.data.get("url")

        if not repository_url:
            return Response(
                {"error": "Repository URL is required. "},
                status = status.HTTP_400_BAD_REQUEST    
            ) 
        
        try:
            
            data = AnalyzerService.analyze_repository(repository_url)

            return Response(data)
        
        except Exception as e: 

            return Response(
                {"error": str(e)},
                status = status.HTTP_400_BAD_REQUEST    
            )



class RepositoryListView(ListAPIView):

    queryset = Repository.objects.all().order_by("-updated_at")
    serializer_class = RepositorySerializer



class RepositoryDetailView(RetrieveAPIView):

    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer



    
