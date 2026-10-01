
from smtplib import SMTPException
import requests
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from .models import ApprovalLog, Article, Newsletter, Publisher
from .permissions import ArticlePermission, NewsletterPermission, can_edit, is_editor
from .serializers import ArticleSerializer, NewsletterSerializer, PublisherSerializer
from .services import approve_article


class ArticleViewSet(ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [ArticlePermission]

    def get_queryset(self):
        query = Article.objects.select_related("author", "publisher")
        if self.action in ("list", "subscribed"):
            return query.filter(approved=True)
        user = self.request.user
        if is_editor(user):
            return query.filter(
                Q(approved=True) | Q(publisher=None) | Q(publisher__editors=user)
            ).distinct()
        return query.filter(Q(approved=True) | Q(author=user))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        # An edited article must go through editorial review again.
        article = serializer.save(approved=False)
        ApprovalLog.objects.filter(article=article).delete()
        if hasattr(article, "delivery"):
            article.delivery.delete()

    @action(detail=False)
    def subscribed(self, request):
        if request.user.role != "reader":
            return Response({"detail": "Reader account required."}, status=403)
        query = Q(publisher__in=request.user.subscribed_publishers.all()) | Q(
            author__in=request.user.subscribed_journalists.all()
        )
        return Response(
            self.get_serializer(
                self.get_queryset().filter(query).distinct(), many=True
            ).data
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        article = self.get_object()
        try:
            article = approve_article(article, request.user)
        except (requests.RequestException, SMTPException, OSError):
            return Response(
                {
                    "detail": "Approved, but delivery failed. "
                    "Retry approval to finish delivery."
                },
                status=502,
            )
        return Response(self.get_serializer(article).data)


class NewsletterViewSet(ModelViewSet):
    queryset = Newsletter.objects.prefetch_related("articles")
    serializer_class = NewsletterSerializer
    permission_classes = [NewsletterPermission]

    def get_queryset(self):
        # Do not expose drafts through an older newsletter after article edits.
        queryset = super().get_queryset()
        if self.action not in ("list", "retrieve"):
            return queryset
        return queryset.exclude(articles__approved=False).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PublisherViewSet(ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approved_log(request):
    if not is_editor(request.user):
        return Response(status=403)
    article_id = request.data.get("article")
    if type(article_id) is not int:
        return Response({"article": "An integer article ID is required."}, status=400)
    article = get_object_or_404(Article, pk=article_id, approved=True)
    if not can_edit(request.user, article):
        return Response(status=403)
    receipt, created = ApprovalLog.objects.get_or_create(article=article)
    return Response(
        {"article": article.pk, "logged_at": receipt.logged_at},
        status=201 if created else 200,
    )
