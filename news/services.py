"""Approve once; email readers individually and POST to our logging endpoint."""

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from rest_framework.authtoken.models import Token
from .models import ApprovalDelivery, Article, User
from .permissions import can_edit, is_editor


def approve_article(article, editor):
    if not is_editor(editor) or not can_edit(editor, article):
        raise PermissionDenied
    with transaction.atomic():
        article = Article.objects.select_for_update().get(pk=article.pk)
        if not article.approved:
            article.approved = True
            article.save(update_fields=["approved"])
        delivery, _ = ApprovalDelivery.objects.get_or_create(article=article)
    # The database transaction is committed before the HTTP request: the logging
    # endpoint must be able to read the approved article in another connection.
    if not delivery.emailed:
        subscribers = (
            User.objects.filter(role="reader")
            .filter(
                Q(subscribed_journalists=article.author)
                | Q(subscribed_publishers=article.publisher)
                if article.publisher_id
                else Q(subscribed_journalists=article.author)
            )
            .exclude(email="")
            .values_list("email", flat=True)
            .distinct()
        )
        for email in subscribers:
            send_mail(
                article.title, article.content, settings.DEFAULT_FROM_EMAIL, [email]
            )
        delivery.emailed = True
        delivery.save(update_fields=["emailed"])
    if not delivery.logged:
        token, _ = Token.objects.get_or_create(user=editor)
        response = requests.post(
            settings.APPROVED_API_URL,
            json={"article": article.pk},
            headers={"Authorization": f"Token {token.key}"},
            timeout=10,
        )
        response.raise_for_status()
        delivery.logged = True
        delivery.save(update_fields=["logged"])
    return article
