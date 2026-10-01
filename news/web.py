"""Browser workflows for readers, journalists and editors."""

from smtplib import SMTPException
import requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import ArticleForm, NewsletterForm, RegistrationForm, SubscriptionForm
from .models import Article, Newsletter
from .permissions import can_edit, is_editor
from .services import approve_article


def register(request):
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("home")
    return render(request, "news/form.html", {"form": form, "title": "Register"})


@login_required
def home(request):
    articles = Article.objects.filter(approved=True)
    drafts = Article.objects.filter(author=request.user, approved=False)
    if is_editor(request.user):
        drafts = Article.objects.filter(
            Q(publisher=None) | Q(publisher__editors=request.user)
        ).distinct()
    return render(
        request,
        "news/home.html",
        {
            "articles": articles,
            "drafts": drafts,
            "editor": is_editor(request.user),
            "newsletters": Newsletter.objects.exclude(
                articles__approved=False
            ).distinct(),
        },
    )


@login_required
def subscriptions(request):
    if request.user.role != "reader":
        raise PermissionDenied
    form = SubscriptionForm(
        request.POST if request.method == "POST" else None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("home")
    return render(request, "news/form.html", {"form": form, "title": "Subscriptions"})


@login_required
def edit(request, kind, pk=None):
    model, form_class = (
        (Article, ArticleForm) if kind == "article" else (Newsletter, NewsletterForm)
    )
    item = get_object_or_404(model, pk=pk) if pk else None
    if item:
        if not can_edit(request.user, item):
            raise PermissionDenied
    elif request.user.role != "journalist" and not (
        kind == "newsletter" and is_editor(request.user)
    ):
        raise PermissionDenied
    options = {"user": request.user} if kind == "article" else {}
    form = form_class(
        request.POST if request.method == "POST" else None, instance=item, **options
    )
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        if not pk:
            item.author = request.user
        if kind == "article":
            item.approved = False
        item.save()
        form.save_m2m()
        if kind == "article":
            if hasattr(item, "delivery"):
                item.delivery.delete()
            if hasattr(item, "approval_log"):
                item.approval_log.delete()
        return redirect("home")
    return render(request, "news/form.html", {"form": form, "title": kind.title()})


@login_required
@require_POST
def delete(request, kind, pk):
    model = Article if kind == "article" else Newsletter
    item = get_object_or_404(model, pk=pk)
    if not can_edit(request.user, item):
        raise PermissionDenied
    item.delete()
    return redirect("home")


@login_required
@require_POST
def approve(request, pk):
    article = get_object_or_404(Article, pk=pk)
    try:
        approve_article(article, request.user)
        messages.success(request, "Article approved and delivered.")
    except (requests.RequestException, SMTPException, OSError):
        messages.error(
            request, "Article approved, but delivery failed. Retry to finish delivery."
        )
    return redirect("home")
