from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, NewsletterViewSet, PublisherViewSet, approved_log

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")
router.register("newsletters", NewsletterViewSet)
router.register("publishers", PublisherViewSet)
urlpatterns = [
    path("", include(router.urls)),
    path("token/", obtain_auth_token),
    path("approved/", approved_log),
]
