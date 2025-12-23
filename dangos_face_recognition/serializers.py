from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserFace, Job
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    is_superuser = serializers.BooleanField(default=False, required=False)
    username = serializers.CharField(required=False)

    class Meta(object):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'job', 'is_active', 'date_joined']

class UserFaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFace
        fields = ['id', 'custom_user', 'custom_user_id', 'image', 'embedding', 'created_at']

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'created_at']