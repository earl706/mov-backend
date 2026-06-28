"""Reusable viewset base classes.

`OwnedModelViewSet` enforces the single most repeated rule in the codebase:
a user may only see and mutate rows they own. It scopes the queryset to the
current user and stamps `owner` on create, so individual feature viewsets stay
focused on feature-specific behaviour.
"""
from rest_framework import viewsets

from .permissions import IsOwner


class OwnedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwner]

    def get_queryset(self):
        # `queryset` is defined on subclasses; scope it to the requesting user.
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            return qs.filter(owner=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
