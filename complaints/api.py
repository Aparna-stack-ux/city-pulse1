from rest_framework import serializers, viewsets, permissions
from .models import Complaint

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'description', 'category', 'priority', 'ward_number',
            'location', 'latitude', 'longitude', 'status', 'anonymous',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related('user').all().order_by('-created_at')
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
