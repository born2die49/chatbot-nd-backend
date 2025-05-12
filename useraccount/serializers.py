from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data retrieval and updates.
    Used for the /profile/ endpoint.
    """
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar']
        read_only_fields = ['id', 'email']