from django.contrib import admin
from django.urls import include, path
from news import web

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("news.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("register/", web.register, name="register"),
    path("", web.home, name="home"),
    path("subscriptions/", web.subscriptions, name="subscriptions"),
    path("articles/<int:pk>/approve/", web.approve, name="approve"),
    path("<str:kind>/new/", web.edit, name="new"),
    path("<str:kind>/<int:pk>/edit/", web.edit, name="edit"),
    path("<str:kind>/<int:pk>/delete/", web.delete, name="delete"),
]
