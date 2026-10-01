from django import forms
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from .models import Article, Newsletter, Publisher, User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=[("reader", "Reader"), ("journalist", "Journalist")]
    )

    class Meta:
        model = User
        fields = ("username", "email", "role")


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ("title", "content", "publisher")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publisher"].queryset = Publisher.objects.filter(
            Q(journalists=user) | Q(editors=user)
        ).distinct()


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ("title", "description", "articles")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["articles"].queryset = Article.objects.filter(approved=True)


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("subscribed_publishers", "subscribed_journalists")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subscribed_journalists"].queryset = User.objects.filter(
            role="journalist"
        )
