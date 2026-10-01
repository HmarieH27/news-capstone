"""Success and failure coverage for roles, subscriptions and delivery."""

from unittest.mock import patch
import requests
from django.core import mail
from django.test import Client, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .models import ApprovalLog, Article, Newsletter, Publisher, User


class NewsApiTests(TestCase):
    def setUp(self):
        self.journalist = User.objects.create_user("journalist", role="journalist")
        self.other = User.objects.create_user("other", role="journalist")
        self.editor = User.objects.create_user("editor", role="editor")
        self.reader = User.objects.create_user("reader", email="reader@example.com")
        self.unsubscribed = User.objects.create_user(
            "unsubscribed", email="unsubscribed@example.com"
        )
        self.client = APIClient()
        self.article = Article.objects.create(
            title="News", content="Body", author=self.journalist
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_anonymous_access_and_role_groups(self):
        self.assertEqual(self.client.get("/api/articles/").status_code, 401)
        self.assertEqual(self.client.post("/api/articles/", {}).status_code, 401)
        self.assertTrue(self.reader.groups.filter(name="Reader").exists())
        self.assertTrue(self.reader.has_perm("news.view_article"))
        self.assertFalse(self.reader.has_perm("news.add_article"))

    def test_create_update_delete_and_ownership(self):
        self.authenticate(self.journalist)
        response = self.client.post(
            "/api/articles/",
            {
                "title": "New",
                "content": "Body",
                "approved": True,
                "author": self.other.pk,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["author"], self.journalist.pk)
        self.assertFalse(response.data["approved"])
        self.assertEqual(
            self.client.put(
                f"/api/articles/{self.article.pk}/",
                {"title": "Edit", "content": "Changed"},
            ).status_code,
            200,
        )
        self.authenticate(self.other)
        self.assertEqual(
            self.client.patch(
                f"/api/articles/{self.article.pk}/", {"title": "Stolen"}
            ).status_code,
            404,
        )
        self.article.approved = True
        self.article.save()
        self.assertEqual(
            self.client.delete(f"/api/articles/{self.article.pk}/").status_code, 403
        )
        self.authenticate(self.reader)
        self.assertEqual(
            self.client.post(
                "/api/articles/", {"title": "No", "content": "No"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                f"/api/articles/{self.article.pk}/", {"title": "No", "content": "No"}
            ).status_code,
            403,
        )
        self.authenticate(self.editor)
        self.assertEqual(
            self.client.delete(f"/api/articles/{self.article.pk}/").status_code, 204
        )

    def test_subscriptions_filter_publishers_and_journalists(self):
        publisher = Publisher.objects.create(name="Press")
        published = Article.objects.create(
            title="Publisher",
            content="Body",
            author=self.other,
            publisher=publisher,
            approved=True,
        )
        Article.objects.create(
            title="Excluded", content="Body", author=self.other, approved=True
        )
        self.article.approved = True
        self.article.save()
        self.reader.subscribed_journalists.add(self.journalist)
        self.reader.subscribed_publishers.add(publisher)
        self.authenticate(self.reader)
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(
            {item["id"] for item in response.data}, {self.article.pk, published.pk}
        )
        self.assertEqual(len(self.client.get("/api/articles/").data), 3)
        self.authenticate(self.unsubscribed)
        self.assertEqual(self.client.get("/api/articles/subscribed/").data, [])

    @patch("news.services.requests.post")
    def test_approval_email_logging_and_repeat(self, post):
        self.reader.subscribed_journalists.add(self.journalist)
        self.authenticate(self.editor)
        url = f"/api/articles/{self.article.pk}/approve/"
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.reader.email])
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["json"], {"article": self.article.pk})
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        post.assert_called_once()
        self.assertEqual(
            self.client.post(
                "/api/approved/", {"article": self.article.pk}, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                "/api/approved/", {"article": self.article.pk}, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(ApprovalLog.objects.count(), 1)
        self.assertEqual(
            self.client.post(
                "/api/approved/", {"article": "bad"}, format="json"
            ).status_code,
            400,
        )

    @patch("news.services.requests.post")
    def test_delivery_failure_is_retryable(self, post):
        post.side_effect = requests.Timeout()
        self.authenticate(self.editor)
        url = f"/api/articles/{self.article.pk}/approve/"
        self.assertEqual(self.client.post(url).status_code, 502)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)
        post.side_effect = None
        self.assertEqual(self.client.post(url).status_code, 200)

    def test_wrong_editor_and_missing_article(self):
        publisher = Publisher.objects.create(name="Other press")
        self.article.publisher = publisher
        self.article.save()
        self.authenticate(self.editor)
        self.assertEqual(
            self.client.post(f"/api/articles/{self.article.pk}/approve/").status_code,
            404,
        )
        self.assertEqual(
            self.client.post("/api/articles/99999/approve/").status_code, 404
        )
        self.authenticate(self.journalist)
        self.assertEqual(
            self.client.post(f"/api/articles/{self.article.pk}/approve/").status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/approved/", {"article": self.article.pk}
            ).status_code,
            403,
        )

    def test_newsletters_validation_roles_and_ownership(self):
        self.authenticate(self.journalist)
        url = "/api/newsletters/"
        self.assertEqual(
            self.client.post(
                url, {"title": "Draft", "articles": [self.article.pk]}, format="json"
            ).status_code,
            400,
        )
        self.article.approved = True
        self.article.save()
        response = self.client.post(
            url,
            {"title": "Weekly", "articles": [self.article.pk], "author": self.other.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        newsletter = Newsletter.objects.get()
        self.assertEqual(newsletter.author, self.journalist)
        self.authenticate(self.other)
        self.assertEqual(
            self.client.patch(f"{url}{newsletter.pk}/", {"title": "Bad"}).status_code,
            403,
        )
        self.authenticate(self.reader)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"title": "No"}).status_code, 403)
        self.authenticate(self.editor)
        self.assertEqual(self.client.delete(f"{url}{newsletter.pk}/").status_code, 204)

    def test_browser_approval_requires_csrf_and_editor(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.editor)
        self.assertContains(browser.get("/"), "Approve")
        self.assertEqual(
            browser.post(f"/articles/{self.article.pk}/approve/").status_code, 403
        )
        self.assertEqual(
            browser.get(f"/articles/{self.article.pk}/approve/").status_code, 405
        )
        browser = Client()
        browser.force_login(self.reader)
        self.assertEqual(
            browser.post(f"/articles/{self.article.pk}/approve/").status_code, 403
        )
        self.assertEqual(browser.get("/subscriptions/").status_code, 200)
