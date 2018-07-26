from rest_framework import permissions


class IsOperator(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Permissions are allowed to the operator(s) of the entity.
        # TODO: Add the operator field to the trip.
        return obj.operator == request.user


default_permissions = (
    permissions.IsAuthenticated,
)
