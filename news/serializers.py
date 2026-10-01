from rest_framework import serializers
from .models import Article, Newsletter, Publisher, User


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"
        read_only_fields = ("approved", "author", "created_at")

    def validate_publisher(self, publisher):
        user = self.context["request"].user
        if publisher and not (
            publisher.journalists.filter(pk=user.pk).exists()
            or publisher.editors.filter(pk=user.pk).exists()
        ):
            raise serializers.ValidationError("You are not a member of this publisher.")
        return publisher


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = "__all__"
        read_only_fields = ("author", "created_at")

    def validate_articles(self, articles):
        if any(not article.approved for article in articles):
            raise serializers.ValidationError(
                "Newsletters may contain only approved articles."
            )
        return articles


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "role")
