from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from django.utils.translation import gettext_lazy as _

OWNER_PERMISSION_MESSAGE = _("You can only modify your own content.")


class IsOwnerOrReadOnly(BasePermission):
    message = OWNER_PERMISSION_MESSAGE

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
