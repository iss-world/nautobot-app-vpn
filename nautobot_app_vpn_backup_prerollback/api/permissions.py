"""Custom API permissions for the Nautobot VPN app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """Allow only staff/superusers to modify data.
    Read-only access is allowed for everyone.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and (request.user.is_staff or request.user.is_superuser)


class IsOwnerOrAdmin(BasePermission):
    """Allow users to modify only objects they own.
    Admins have full access.
    Assumes `obj.created_by` exists; otherwise, denies write access.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Fall back to read-only if `created_by` is not defined
        owner = getattr(obj, "created_by", None)
        if owner is None:
            return False

        return request.user.is_superuser or owner == request.user


class IsAuthenticatedOrAdmin(BasePermission):
    """Allow authenticated users to write.
    Anonymous users get read-only access.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
