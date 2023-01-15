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
from rest_framework.authentication import TokenAuthentication

from core.models import Project

from project import serializers


class ProjectViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Manage projects in the database."""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
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

    def destroy(self, request, *args, **kwargs):
        """Delete a project."""
        instance = self.get_object()
        if instance.author_user_id == self.request.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
