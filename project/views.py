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
    serializer_class = serializers.ProjectDetailSerializer

    def get_queryset(self):
        """Retrieve the projects for users that are project contributors."""
        return Project.objects.filter(
                contributor__user_id=self.request.user).order_by('-id')

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

    def get_queryset(self):
        """Return objecturrent authenticated user only."""
        return Contributor.objects.filter(project_id=self.kwargs['project_pk'])

    def get_serializer_context(self):
        """Add the projet to the serializer context."""
        context = super().get_serializer_context()
        context['project'] = Project.objects.get(
                        id=self.kwargs['project_pk'])
        return context

    def create(self, request, *args, **kwargs):
        """Create a contributor and make sure the project exists."""
        try:
            Project.objects.get(id=self.kwargs['project_pk'])
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return super().create(request, *args, **kwargs)


class IssueViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """Manage issues in the database. The queryset is filtered to only
    show issues for the current project.

    The possible values for the status are :
        - todo (for A faire)
        - in progress (for En cours)
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
    permission_classes = [permissions.IsProjectContributor, IsAuthenticated,
                          permissions.IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return issues for the current project only and only
        if the user is a contributor."""
        return Issue.objects.filter(project_id=self.kwargs['project_pk'])

    def partial_update(self, request, *args, **kwargs):
        """Partial update of an issue is not possible."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_serializer_context(self):
        """Add the project to the serializer context."""
        context = super().get_serializer_context()
        context['project'] = Project.objects.get(id=self.kwargs['project_pk'])
        context['assignee_user_id'] = self.request.data.get(
            'assignee_user_id')
        return context

    def perform_create(self, serializer):
        """Create a new issue."""
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
    permission_classes = [permissions.IsProjectContributor, IsAuthenticated,
                          permissions.IsOwnerOrReadOnly]

    def get_queryset(self):
        """Filter queryset for current issue."""
        return Comment.objects.filter(issue_id=self.kwargs['issue_pk'])

    def partial_update(self, request, *args, **kwargs):
        """Partial update of an issue is not possible."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_create(self, serializer):
        """Create a new project."""
        issue_id = self.kwargs['issue_pk']
        issue = Issue.objects.get(id=issue_id)
        serializer.save(author_user_id=self.request.user,
                        issue_id=issue)
