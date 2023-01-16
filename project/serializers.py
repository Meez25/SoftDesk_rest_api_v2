"""
Serializers for the project APIs.
"""
from rest_framework import serializers

from core.models import Project, Contributor, User, Issue


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project objects."""
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'type', 'author_user_id')
        read_only_fields = ('id',)
        extra_kwargs = {
            'description': {'write_only': True},
        }


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

    def validate_permission(self, value):
        """Validate the permission field."""
        possible_permissions = []
        for permission in Contributor.PERMISSION_CHOICES:
            possible_permissions.append(permission[0])
        if value not in possible_permissions:
            raise serializers.ValidationError(
                    'Permission must be one of the following: '
                    '{}'.format(', '.join(possible_permissions))
                    )
        return value


class IssueSerializer(serializers.ModelSerializer):
    """Serializer for issue objects."""
    class Meta:
        model = Issue
        fields = ('id',
                  'title',
                  'description',
                  'tag',
                  'author_user_id',
                  'project_id',
                  'status',
                  'priority',
                  'created_time',
                  'assignee_user_id',
                  )
        read_only_fields = ('id',)
