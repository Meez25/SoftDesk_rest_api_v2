"""
Serializers for the project APIs.
"""
from rest_framework import serializers

from core.models import Project, Contributor


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project objects."""
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'type', 'author_user_id')
        read_only_fields = ('id',)
        extra_kwargs = {
            'description': {'write_only': True},
        }

    def create(self, validated_data):
        """Create a project."""
        return Project.objects.create(**validated_data)

    def save(self, **kwargs):
        """Save the project and add the user as a contributor."""
        project = super().save(**kwargs)
        contributor = Contributor.objects.create(
            project_id=project,
            user_id=self.context['request'].user,
            permission='owner',
            role='owner',
            )
        contributor.save()


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


class ContributorSerializer(serializers.ModelSerializer):
    """Serializer for contributor objects."""
    class Meta:
        model = Contributor
        fields = ('id', 'project_id', 'user_id', 'permission', 'role')
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Create a contributor with correct permissions."""
        return Contributor.objects.create(**validated_data)
