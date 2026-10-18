from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article, Category


class NewsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username="reporter", password="test-password")
        cls.category = Category.objects.create(name="Lifestyle", slug="lifestyle")
        cls.other_category = Category.objects.create(name="Travel", slug="travel")
        cls.articles = [
            Article.objects.create(
                title=f"Story {i}", slug=f"story-{i}", content=f"Content {i}",
                author=cls.author, category=cls.category, is_published=True,
                is_trending=(i == 0),
            )
            for i in range(12)
        ]
        cls.other_article = Article.objects.create(
            title="Travel story", slug="travel-story", content="Travel text",
            author=cls.author, category=cls.other_category, is_published=True,
        )
        cls.draft = Article.objects.create(
            title="Secret draft", slug="secret-draft", content="Private",
            author=cls.author, category=cls.category, is_published=False, is_trending=True,
        )

    def test_home_shows_only_published_articles_and_category_tabs(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Story 0")
        self.assertContains(response, "Lifestyle")
        self.assertNotContains(response, "Secret draft")
        self.assertEqual(list(response.context["trending_articles"]), [self.articles[0]])

    def test_category_filters_and_paginates_articles(self):
        response = self.client.get(reverse("category", args=["lifestyle"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["articles"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertNotContains(response, "Travel story")
        self.assertEqual(len(self.client.get(reverse("category", args=["lifestyle"]), {"page": "invalid"}).context["articles"]), 10)
        self.assertEqual(len(self.client.get(reverse("category", args=["lifestyle"]), {"page": "999"}).context["articles"]), 2)

    def test_unknown_category_returns_404(self):
        self.assertEqual(self.client.get(reverse("category", args=["missing"])).status_code, 404)

    def test_latest_news_orders_and_paginates_published_articles(self):
        response = self.client.get(reverse("latest_news"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["articles"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)
        self.assertNotContains(response, "Secret draft")
        self.assertEqual(response.context["articles"][0], self.other_article)
        self.assertEqual(len(self.client.get(reverse("latest_news"), {"page": "2"}).context["articles"]), 3)

    def test_detail_increments_counter_and_shows_related_articles(self):
        response = self.client.get(reverse("details", args=["story-0"]))
        self.assertEqual(response.status_code, 200)
        self.articles[0].refresh_from_db()
        self.assertEqual(self.articles[0].views_count, 1)
        self.assertContains(response, "Story 1")
        self.assertNotContains(response, "Travel story")
        self.assertNotContains(response, "Secret draft")

    def test_unpublished_or_missing_detail_returns_404_without_increment(self):
        self.assertEqual(self.client.get(reverse("details", args=["secret-draft"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("details", args=["unknown"])).status_code, 404)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views_count, 0)
