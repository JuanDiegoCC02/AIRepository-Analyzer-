from rest_framework import serializers 

from api.models.analysis import Analysis

class AnalysisSerializer(serializers.ModelSerializer):

    class Meta: 
        model = Analysis
        fields = "__all__"