from io import BytesIO
import sys
from pathlib import Path
from types import ModuleType

from django.contrib.auth import get_user_model
from django.conf import settings
from django.conf.urls.static import static
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .admin import ArticleAdmin, CommentAdmin, approve_comments, reject_comments
from .context_processors import global_categories, social_links
from .models import Article, Category, Comment
from djangoproj import urls as project_urls


class PhaseFiveContextProcessorTests(TestCase):
    def test_categories_are_ordered_and_reused_for_the_request(self):
        Category.objects.create(name="Travel", slug="travel")
        Category.objects.create(name="Arts", slug="arts")
        request = RequestFactory().get("/")

        first = global_categories(request)["global_categories"]
        second = global_categories(request)["global_categories"]

        self.assertIs(first, second)
        self.assertEqual([category.name for category in first], ["Arts", "Travel"])

    @override_settings(SOCIAL_LINKS={"facebook": "https://example.com/fb", "x": ""})
    def test_social_context_only_includes_configured_urls(self):
        links = social_links(RequestFactory().get("/"))["social_links"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["platform"], "facebook")
        self.assertEqual(links[0]["url"], "https://example.com/fb")

    @override_settings(SOCIAL_LINKS={"instagram": "https://example.com/ig"})
    def test_global_context_is_used_in_navigation_and_footer(self):
        Category.objects.create(name="Local News", slug="local-news")
        response = self.client.get(reverse("home"))

        self.assertContains(response, "/category/local-news/")
        self.assertContains(response, 'aria-label="Instagram"')
        self.assertContains(response, 'href="https://example.com/ig"')


class PhaseFiveAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="editor", password="test-password", email="editor@example.com",
        )
        cls.category = Category.objects.create(name="News", slug="news")
        cls.article = Article.objects.create(
            title="A story", slug="a-story", author=cls.user,
            category=cls.category, content="<p>Existing article</p>",
        )

    def test_article_admin_uses_summernote_for_content(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:news_article_change", args=[self.article.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "summernote")
        self.assertContains(response, "Existing article")
        self.assertEqual(ArticleAdmin.summernote_fields, ("content",))
        self.assertIn("views_count", ArticleAdmin.readonly_fields)

    def test_comment_admin_actions_approve_and_reject(self):
        comment = Comment.objects.create(
            article=self.article, name="Reader", email="reader@example.com",
            content="A comment", is_approved=False,
        )

        approve_comments(None, None, Comment.objects.filter(pk=comment.pk))
        comment.refresh_from_db()
        self.assertTrue(comment.is_approved)

        reject_comments(None, None, Comment.objects.filter(pk=comment.pk))
        comment.refresh_from_db()
        self.assertFalse(comment.is_approved)
        self.assertIn("is_approved", CommentAdmin.list_editable)

    def test_upload_requires_staff_and_accepts_an_image(self):
        upload_url = "/summernote/upload_attachment/"
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()

        self.client.force_login(get_user_model().objects.create_user(
            username="reader", password="test-password", is_staff=False,
        ))
        denied = self.client.post(upload_url, {"files": SimpleUploadedFile(
            "pixel.png", image_bytes, content_type="image/png",
        )})
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.user)
        response = self.client.post(upload_url, {"files": SimpleUploadedFile(
            "pixel.png", image_bytes, content_type="image/png",
        )})
        self.assertEqual(response.status_code, 200, response.content)
        image_url = response.json()["files"][0]["url"]
        self.assertIn("/media/django-summernote/", image_url)
        uploaded_path = Path(settings.MEDIA_ROOT, image_url.removeprefix(settings.MEDIA_URL))
        self.assertTrue(uploaded_path.is_file(), str(uploaded_path))
        urlconf_name = "news.tests_phase5_media_urlconf"
        media_urlconf = ModuleType(urlconf_name)
        with override_settings(DEBUG=True):
            media_urlconf.urlpatterns = project_urls.urlpatterns + static(
                settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
            )
        sys.modules[urlconf_name] = media_urlconf
        try:
            with override_settings(DEBUG=True, ROOT_URLCONF=urlconf_name):
                media_response = self.client.get(image_url)
            self.assertEqual(media_response.status_code, 200)
            self.assertEqual(media_response["Content-Type"], "image/png")
        finally:
            if "media_response" in locals():
                media_response.close()
            uploaded_path.unlink(missing_ok=True)
            sys.modules.pop(urlconf_name, None)


class PhaseFiveRichTextTests(TestCase):
    def test_rich_text_filter_strips_script_and_keeps_editor_formatting(self):
        from django.template import engines

        template = engines["django"].from_string(
            "{% load news_tags %}{{ value|rich_text }}"
        )
        rendered = template.render({"value": '<h2 style="text-align: center">Title</h2><script>alert(1)</script><p><strong>Safe</strong></p>'})

        self.assertIn("<h2", rendered)
        self.assertIn("text-align: center", rendered)
        self.assertIn("<strong>Safe</strong>", rendered)
        self.assertNotIn("<script", rendered)
