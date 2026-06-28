from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Object-level permission: only the owner may access the object.

    Works with any model exposing an `owner` attribute. List querysets should
    additionally be filtered by owner in the view (see OwnedModelViewSet).
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "owner", None)
        return owner is not None and owner == request.user
