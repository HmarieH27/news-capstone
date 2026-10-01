from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    role = models.CharField(
        max_length=12,
        choices=[
            ("reader", "Reader"),
            ("editor", "Editor"),
            ("journalist", "Journalist"),
        ],
        default="reader",
    )
    subscribed_publishers = models.ManyToManyField(
        "Publisher", blank=True, related_name="subscribers"
    )
    subscribed_journalists = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="journalist_subscribers"
    )


class Publisher(models.Model):
    name = models.CharField(max_length=150)
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="edited_publishers"
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="publishers"
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articles"
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="newsletters"
    )
    articles = models.ManyToManyField(Article, related_name="newsletters")


class ApprovalLog(models.Model):

    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="approval_log"
    )
    logged_at = models.DateTimeField(auto_now_add=True)


class ApprovalDelivery(models.Model):

    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="delivery"
    )
    emailed = models.BooleanField(default=False)
    logged = models.BooleanField(default=False)
