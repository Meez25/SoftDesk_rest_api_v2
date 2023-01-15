"""
Views for the project APIs.
"""
from rest_framework import (
        viewsets,
        mixins,
        status,
        )
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Project

from project import serializers
from project import permissions


class ProjectViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Manage projects in the database."""

    permission_classes = (IsAuthenticated, permissions.IsOwnerOrReadOnly)
    queryset = Project.objects.all()
    serializer_class = serializers.ProjectDetailSerializer

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        return self.queryset.all().order_by('-id')

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list' or self.action == 'create':
            return serializers.ProjectSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new project."""
        serializer.save(author_user_id=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        """Partial update of a project is not possible."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
