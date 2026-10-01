"""Keep each user's role group and its Django permissions in sync."""

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.management import create_permissions
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import User


@receiver(post_migrate)
def configure_groups(sender, **kwargs):
    if sender.name != "news":
        return
    create_permissions(sender, verbosity=0)
    for role, actions in {
        "Reader": ["view"],
        "Editor": ["view", "change", "delete"],
        "Journalist": ["view", "add", "change", "delete"],
    }.items():
        group, _ = Group.objects.get_or_create(name=role)
        codes = [
            f"{action}_{model}"
            for action in actions
            for model in ("article", "newsletter")
        ]
        group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="news", codename__in=codes
            )
        )


@receiver(post_save, sender=User)
def sync_role(sender, instance, raw=False, **kwargs):
    if raw:
        return
    groups = Group.objects.filter(name__in=["Reader", "Editor", "Journalist"])
    instance.groups.remove(*groups)
    group, _ = Group.objects.get_or_create(name=instance.role.title())
    instance.groups.add(group)
    if instance.role != "reader":
        instance.subscribed_publishers.clear()
        instance.subscribed_journalists.clear()
