from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Publisher, Article, Newsletter, ApprovalLog


@admin.register(User)
class NewsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("News role", {"fields": ("role",)}),)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # Approval must run through the delivery service via the editorial UI.
    readonly_fields = ("approved",)


admin.site.register([Publisher, Newsletter, ApprovalLog])
