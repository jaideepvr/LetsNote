from rest_framework import serializers
from .models import Notes, Note_Tag
from users.serializers import UserSerializer


class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = Notes
        fields = ('title', 'note_text', 'tags')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note_Tag
        fields = ('tag_text',)
