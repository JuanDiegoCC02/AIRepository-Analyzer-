from rest_framework import serializers

from api.models.repository import Repository



class RepositorySerializer(serializers.ModelSerializer):

    class Meta: 

        model = Repository

        fields = [
            "id",
            "owner",
            "name",
            "html_url",
            "created_at", 
            "updated_at", 
        ]
        