from rest_framework import permissions

from core.models import Contributor


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'author_user_id'):
            return obj.author_user_id == request.user


class isProjectOwner(permissions.BasePermission):
    """Custom permission for contributors."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        project_owner = Contributor.objects.filter(
            project_id=obj.project_id,
            permission='OWN',
            )
        owner_id = [owner.user_id.id for owner in project_owner]
        if request.user.id in owner_id:
            return True
        return False


class isProjectContributor(permissions.BasePermission):
    """Custom permission for contributors."""

    def has_object_permission(self, request, view, obj):
        project_contributor = Contributor.objects.filter(
            project_id=obj.project_id,
            )
        contributor_id = [cont.user_id.id for cont in project_contributor]
        if request.user.id in contributor_id:
            return True
        return False

    def has_permission(self, request, view):
        project_contributor = Contributor.objects.filter(
            project_id=view.kwargs['project_pk'],
            )
        contributor_id = [cont.user_id.id for cont in project_contributor]
        if request.user.id in contributor_id:
            return True
        return False
