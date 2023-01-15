"""
Serializers for the project APIs.
"""
from rest_framework import serializers

from core.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project objects."""
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'type', 'author_user_id')
        read_only_fields = ('id',)
        write_only_fields = ('description',)

    def create(self, validated_data):
        """Create a project."""
        return Project.objects.create(**validated_data)


class ProjectDetailSerializer(ProjectSerializer):
    """Serializer for project detail."""
    author_user_id = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'type', 'author_user_id')
        read_only_fields = ('id',)

    def get_author_user_id(self, obj):
        """Get the author user id."""
        return obj.author_user_id.id
