"""Role and ownership rules shared by the HTML and API views."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_editor(user):
    return user.is_authenticated and (
        user.role == "editor" or user.groups.filter(name="Editor").exists()
    )


def can_edit(user, obj):
    if is_editor(user):
        publisher = getattr(obj, "publisher", None)
        return publisher is None or publisher.editors.filter(pk=user.pk).exists()
    return user.role == "journalist" and obj.author_id == user.pk


class ArticlePermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if view.action == "approve":
            return is_editor(user)
        if request.method in SAFE_METHODS:
            return True
        if request.method == "POST":
            return user.role == "journalist"
        return user.role == "journalist" or is_editor(user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.approved or can_edit(request.user, obj)
        return can_edit(request.user, obj)


class NewsletterPermission(ArticlePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.method == "POST":
            return request.user.role == "journalist" or is_editor(request.user)
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or can_edit(request.user, obj)
