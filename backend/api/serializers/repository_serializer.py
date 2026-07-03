from rest_framework improt serializers
from api.models import Repository

class RepositorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Repository
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", )
        