from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    notes = serializers.StringRelatedField(many=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'notes')
