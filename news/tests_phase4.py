from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article, Category, Comment, ContactMessage, Subscriber


class PhaseFourTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = get_user_model().objects.create_user(username="phase4-reporter")
        category = Category.objects.create(name="Technology", slug="technology")
        cls.article = Article.objects.create(
            title="Technology Update", slug="technology-update", content="Mixed CASE content",
            author=author, category=category, is_published=True,
        )
        Article.objects.create(
            title="Unpublished Technology", slug="draft-technology", content="hidden",
            author=author, category=category, is_published=False,
        )

    def test_category_index_loads_without_a_slug(self):
        response = self.client.get(reverse("category_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All Categories")
        self.assertContains(response, "Technology Update")

    def test_old_relative_category_url_redirects_to_category_index(self):
        response = self.client.get("/contact/categori.html")
        self.assertRedirects(response, reverse("category_index"))

    def test_contact_page_uses_django_post_without_legacy_ajax_script(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/contact/"')
        self.assertNotContains(response, "contact.js")

    def test_search_is_case_insensitive_and_only_published(self):
        response = self.client.get(reverse("search"), {"q": "tEcHnOlOgY"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result_count"], 1)
        self.assertContains(response, "Technology Update")
        self.assertNotContains(response, "Unpublished Technology")

    def test_search_matches_article_content_case_insensitively(self):
        response = self.client.get(reverse("search"), {"q": "cAsE"})
        self.assertEqual(response.context["result_count"], 1)
        self.assertContains(response, "Technology Update")

    def test_empty_search_prompts_instead_of_listing_every_article(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result_count"], 0)
        self.assertContains(response, "Enter a search term")
        self.assertNotContains(response, "Technology Update")

    def test_search_paginates_after_ten_results(self):
        for index in range(10):
            Article.objects.create(
                title=f"Technology Extra {index}", slug=f"technology-extra-{index}",
                content="More results", author=self.article.author,
                category=self.article.category, is_published=True,
            )
        response = self.client.get(reverse("search"), {"q": "technology"})
        self.assertEqual(response.context["result_count"], 11)
        self.assertEqual(len(response.context["articles"]), 10)
        second_page = self.client.get(reverse("search"), {"q": "technology", "page": 2})
        self.assertEqual(len(second_page.context["articles"]), 1)

    def test_comment_is_saved_unapproved_and_redirected(self):
        response = self.client.post(reverse("details", args=[self.article.slug]), {
            "name": "Reader", "email": "reader@example.com", "content": "A comment",
        })
        self.assertRedirects(response, reverse("details", args=[self.article.slug]))
        comment = Comment.objects.get()
        self.assertEqual(comment.article, self.article)
        self.assertFalse(comment.is_approved)
        self.assertNotContains(self.client.get(reverse("details", args=[self.article.slug])), "A comment")

    def test_approved_comments_are_public(self):
        Comment.objects.create(
            article=self.article, name="Reader", email="reader@example.com",
            content="Approved comment", is_approved=True,
        )
        response = self.client.get(reverse("details", args=[self.article.slug]))
        self.assertContains(response, "Approved comment")
        self.assertContains(response, "Comments (1)")

    def test_invalid_comment_is_not_saved(self):
        response = self.client.post(reverse("details", args=[self.article.slug]), {
            "name": "Reader", "email": "invalid", "content": "Rejected comment",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address")

    def test_contact_message_is_saved_and_redirects(self):
        response = self.client.post(reverse("contact"), {
            "name": "Reader", "email": "reader@example.com", "subject": "Hello", "message": "Contact text",
        })
        self.assertRedirects(response, reverse("contact"))
        self.assertEqual(ContactMessage.objects.get().subject, "Hello")

    def test_contact_invalid_email_is_rejected(self):
        response = self.client.post(reverse("contact"), {
            "name": "Reader", "email": "invalid", "subject": "Hello", "message": "Contact text",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address")

    def test_invalid_newsletter_email_is_not_saved(self):
        self.client.post(reverse("subscribe"), {"email": "invalid", "next": "/"})
        self.assertEqual(Subscriber.objects.count(), 0)

    def test_footer_newsletter_form_posts_email_to_django(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'action="/newsletter/subscribe/"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_newsletter_normalizes_email_and_handles_duplicate(self):
        url = reverse("subscribe")
        self.client.post(url, {"email": "Reader@Example.com", "next": "/"})
        self.client.post(url, {"email": "reader@example.com", "next": "/"})
        self.assertEqual(Subscriber.objects.count(), 1)
        self.assertEqual(Subscriber.objects.get().email, "reader@example.com")
