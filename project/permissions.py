from rest_framework import permissions

from core.models import Contributor


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'author_user_id'):
            return obj.author_user_id == request.user


class ContributorPermission(permissions.BasePermission):
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
