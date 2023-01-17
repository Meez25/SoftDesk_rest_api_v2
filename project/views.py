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

from core.models import Project, Contributor, Issue, Comment

from project import serializers
from project import permissions


class ProjectViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Manage projects in the database.
    The possible values for the type are :
        - back (for Back-end)
        - front (for Front-end)
        - iOS (for iOS)
        - android (for Android)."""

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


class ContributorViewSet(mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """Manage contributors in the database. The queryset is filtered to only
    show contributors for the current project.
    The possible values for the permission are :
        - CTR (for Contributor)
        - OWN (for Owner).
    """

    permission_classes = [IsAuthenticated, permissions.IsProjectOwner]
    serializer_class = serializers.ContributorSerializer
    queryset = Contributor.objects.all()

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(project_id=self.kwargs['project_pk'])


class IssueViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """Manage issues in the database. The queryset is filtered to only
    show issues for the current project.

    The possible values for the status are :
        - todo (for A faire)
        - in_progress (for En cours)
        - done (for Terminé).

    The possible values for the priority are :
        - low (for Faible)
        - medium (for Moyenne)
        - high (for Haute)

    The possible values for the tag are :
        - bug (for Bug)
        - improvement (for Amélioration)
        - task (for Tâche)
    """

    serializer_class = serializers.IssueSerializer
    queryset = Issue.objects.all()
    permission_classes = [permissions.IsProjectContributor, IsAuthenticated,
                          permissions.IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return issues for the current project only and only
        if the user is a contributor."""
        return self.queryset.filter(project_id=self.kwargs['project_pk'])

    def partial_update(self, request, *args, **kwargs):
        """Partial update of an issue is not possible."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_create(self, serializer):
        """Create a new issue."""
        if not self.request.data.get('assignee_user_id'):
            serializer.save(author_user_id=self.request.user,
                            assignee_user_id=self.request.user)
        serializer.save(author_user_id=self.request.user)


class CommentViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """Manage comments in the database. The queryset is filtered to only
    show comments for the current issue."""

    serializer_class = serializers.CommentSerializer
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsProjectContributor, IsAuthenticated,
                          permissions.IsOwnerOrReadOnly]

    def partial_update(self, request, *args, **kwargs):
        """Partial update of an issue is not possible."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_create(self, serializer):
        """Create a new project."""
        serializer.save(author_user_id=self.request.user)
