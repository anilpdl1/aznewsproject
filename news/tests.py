from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article, Category, Comment


class NewsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(
            username="reporter", password="test-password"
        )
        cls.category = Category.objects.create(name="Lifestyle", slug="lifestyle")
        cls.other_category = Category.objects.create(name="Travel", slug="travel")
        cls.articles = [
            Article.objects.create(
                title=f"Story {i}",
                slug=f"story-{i}",
                content=f"Content {i}",
                author=cls.author,
                category=cls.category,
                is_published=True,
                is_trending=(i == 0),
            )
            for i in range(12)
        ]
        cls.other_article = Article.objects.create(
            title="Travel story",
            slug="travel-story",
            content="Travel text",
            author=cls.author,
            category=cls.other_category,
            is_published=True,
        )
        cls.draft = Article.objects.create(
            title="Secret draft",
            slug="secret-draft",
            content="Private",
            author=cls.author,
            category=cls.category,
            is_published=False,
            is_trending=True,
        )

    def test_home_shows_only_published_articles_and_category_tabs(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Story 0")
        self.assertContains(response, "Lifestyle")
        self.assertNotContains(response, "Secret draft")
        self.assertEqual(
            list(response.context["trending_articles"]), [self.articles[0]]
        )

    def test_home_trending_section_only_contains_published_trending_articles(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        trending_html = (
            response.content.decode()
            .split('<div class="trending-area fix">', 1)[1]
            .split("<!-- Trending Area End -->", 1)[0]
        )
        self.assertIn("Story 0", trending_html)
        self.assertNotIn("Story 1", trending_html)
        self.assertNotIn("Secret draft", trending_html)
        self.assertIn(reverse("details", args=["story-0"]), trending_html)
        self.assertIn("img/trending/trending_top.jpg", trending_html)
        self.assertEqual(len(response.context["trending_articles"]), 1)
        self.assertContains(response, "weekly-news-active")
        self.assertContains(response, "weekly2-news-active")
        self.assertContains(response, "youtube-area")
        self.assertContains(response, "recent-active")
        html = response.content.decode()
        self.assertEqual(
            html.count('src="https://www.youtube.com/embed/CicQIuG8hBo"'), 2
        )
        self.assertEqual(html.count('class="video-items text-center"'), 5)
        self.assertEqual(html.count('class="single-video"'), 5)

    def test_ticker_and_weekly_carousels_use_published_articles_and_detail_links(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        ticker_html = html.split('<ul id="js-news"', 1)[1].split("</ul>", 1)[0]
        weekly_html = html.split('class="weekly-news-active', 1)[1].split(
            "<!-- End Weekly-News -->", 1
        )[0]
        weekly2_html = html.split('class="weekly2-news-active', 1)[1].split(
            "<!-- End Weekly2-News -->", 1
        )[0]

        self.assertEqual(len(response.context["ticker_articles"]), 5)
        self.assertEqual(
            list(response.context["weekly_articles"]),
            list(response.context["recent_articles"]),
        )
        self.assertEqual(
            list(response.context["weekly2_articles"]),
            list(response.context["ticker_articles"]),
        )
        self.assertIn("Travel story", ticker_html)
        self.assertIn(reverse("details", args=["travel-story"]), ticker_html)
        self.assertNotIn("Secret draft", html)
        self.assertNotIn("Welcome To The Best Model Winner Contest", weekly_html)
        self.assertNotIn("Welcome To The Best Model Winner Contest", weekly2_html)
        self.assertIn("Story 11", weekly_html)
        self.assertIn("Travel story", weekly2_html)
        self.assertIn(reverse("details", args=["travel-story"]), weekly2_html)

    def test_home_whats_new_tabs_filter_by_category_and_link_articles(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        all_tab_html = html.split('id="nav-home"', 1)[1].split('id="nav-panel-1"', 1)[0]
        lifestyle_tab_html = html.split('id="nav-panel-1"', 1)[1].split(
            'id="nav-panel-2"', 1
        )[0]
        travel_tab_html = html.split('id="nav-panel-2"', 1)[1].split(
            'id="nav-panel-3"', 1
        )[0]
        sports_tab_html = html.split('id="nav-panel-4"', 1)[1].split(
            'id="nav-panel-5"', 1
        )[0]

        self.assertEqual(response.context["all_published_articles"].count(), 13)
        self.assertEqual(response.context["lifestyle_articles"].count(), 12)
        self.assertEqual(response.context["travel_articles"].count(), 1)
        self.assertEqual(response.context["fashion_articles"].count(), 0)
        self.assertEqual(response.context["sports_articles"].count(), 0)
        self.assertEqual(response.context["technology_articles"].count(), 0)
        self.assertIn("Travel story", all_tab_html)
        self.assertIn("Story 0", all_tab_html)
        self.assertIn("Story 11", lifestyle_tab_html)
        self.assertNotIn("Travel story", lifestyle_tab_html)
        self.assertIn("Travel story", travel_tab_html)
        self.assertIn("No published articles in Sports yet.", sports_tab_html)
        self.assertIn('href="#nav-panel-4"', html)
        self.assertIn('aria-controls="nav-panel-4"', html)
        self.assertIn('id="nav-panel-4"', html)
        self.assertIn(reverse("details", args=["travel-story"]), all_tab_html)
        self.assertIn(reverse("category", args=["travel"]), all_tab_html)
        self.assertIn("img/news/whatNews1.jpg", html)
        self.assertNotIn("Secret draft", html)

    def test_home_recent_articles_are_newest_published_articles(self):
        response = self.client.get(reverse("home"))
        recent_html = (
            response.content.decode()
            .split('<div class="recent-articles">', 1)[1]
            .split("<!-- Recent Articles End -->", 1)[0]
        )
        recent_articles = list(response.context["recent_articles"])

        self.assertEqual(len(recent_articles), 4)
        self.assertEqual(len({article.pk for article in recent_articles}), 4)
        self.assertEqual(recent_articles[0], self.other_article)
        self.assertIn("Travel story", recent_html)
        self.assertIn(reverse("details", args=["travel-story"]), recent_html)
        self.assertNotIn("Secret draft", recent_html)
        self.assertIn("img/news/recent1.jpg", recent_html)

    def test_category_filters_and_paginates_articles(self):
        response = self.client.get(reverse("category", args=["lifestyle"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["articles"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertNotContains(response, "Travel story")
        self.assertContains(response, "?page=2")
        self.assertIn(
            reverse("category", args=["lifestyle"]), response.request["PATH_INFO"]
        )
        second_page = self.client.get(
            reverse("category", args=["lifestyle"]), {"page": "2"}
        )
        self.assertEqual(len(second_page.context["articles"]), 2)
        self.assertTrue(
            all(
                article.category == self.category
                for article in second_page.context["articles"]
            )
        )
        self.assertEqual(
            len(
                self.client.get(
                    reverse("category", args=["lifestyle"]), {"page": "invalid"}
                ).context["articles"]
            ),
            10,
        )
        self.assertEqual(
            len(
                self.client.get(
                    reverse("category", args=["lifestyle"]), {"page": "999"}
                ).context["articles"]
            ),
            2,
        )

    def test_unknown_category_returns_404(self):
        self.assertEqual(
            self.client.get(reverse("category", args=["missing"])).status_code, 404
        )

    def test_latest_news_orders_and_paginates_published_articles(self):
        response = self.client.get(reverse("latest_news"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["articles"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)
        self.assertNotContains(response, "Secret draft")
        self.assertEqual(response.context["articles"][0], self.other_article)
        self.assertContains(response, "?page=2")
        self.assertEqual(
            len(
                self.client.get(reverse("latest_news"), {"page": "2"}).context[
                    "articles"
                ]
            ),
            3,
        )

    def test_detail_increments_counter_and_shows_related_articles(self):
        response = self.client.get(reverse("details", args=["story-0"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Content 0")
        self.assertContains(response, "Story 0")
        self.articles[0].refresh_from_db()
        self.assertEqual(self.articles[0].views_count, 1)
        self.assertContains(response, "Story 1")
        self.assertNotContains(response, "Travel story")
        self.assertNotContains(response, "Secret draft")
        self.assertLessEqual(len(response.context["related_articles"]), 4)
        self.assertNotIn(self.articles[0], response.context["related_articles"])
        self.assertNotIn(self.draft, response.context["related_articles"])

        self.client.get(reverse("details", args=["story-0"]))
        self.articles[0].refresh_from_db()
        self.assertEqual(self.articles[0].views_count, 2)

    def test_unpublished_or_missing_detail_returns_404_without_increment(self):
        self.assertEqual(
            self.client.get(reverse("details", args=["secret-draft"])).status_code, 404
        )
        self.assertEqual(
            self.client.get(reverse("details", args=["unknown"])).status_code, 404
        )
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views_count, 0)

    def test_detail_shows_only_approved_comments(self):
        approved_comment = Comment.objects.create(
            article=self.articles[0],
            name="Approved reader",
            email="approved@example.com",
            message="Visible comment",
            is_approved=True,
        )
        Comment.objects.create(
            article=self.articles[0],
            name="Pending reader",
            email="pending@example.com",
            message="Hidden until approved",
        )

        response = self.client.get(reverse("details", args=["story-0"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible comment")
        self.assertNotContains(response, "Hidden until approved")
        self.assertEqual(list(response.context["comments"]), [approved_comment])

    def test_comment_submission_is_saved_pending_approval(self):
        response = self.client.post(
            reverse("details", args=["story-0"]),
            {
                "name": "New reader",
                "email": "new@example.com",
                "message": "Please review this comment.",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("details", args=["story-0"]))
        comment = Comment.objects.get(article=self.articles[0])
        self.assertFalse(comment.is_approved)
        self.assertEqual(self.articles[0].views_count, 0)

        self.assertContains(response, "submitted for review")
        self.assertNotContains(response, "Please review this comment.")

    def test_invalid_comment_submission_does_not_create_comment(self):
        response = self.client.post(
            reverse("details", args=["story-0"]),
            {"name": "Reader", "email": "invalid-email", "message": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["comment_form"].errors)
        self.assertFalse(Comment.objects.filter(article=self.articles[0]).exists())


class EmptyHomeViewTests(TestCase):
    def test_home_renders_empty_dynamic_sections(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No trending articles yet.")
        self.assertContains(response, "No published articles yet.")
        self.assertContains(response, "No published articles in Technology yet.")
        self.assertContains(response, "No published articles in Lifestyle yet.")
        self.assertNotContains(response, 'id="js-news"')

        category = Category.objects.create(name="Empty", slug="empty")
        category_response = self.client.get(reverse("category", args=[category.slug]))
        latest_response = self.client.get(reverse("latest_news"))
        self.assertEqual(category_response.status_code, 200)
        self.assertEqual(latest_response.status_code, 200)
        self.assertContains(category_response, "No published articles found.")
        self.assertContains(latest_response, "No published articles found.")
