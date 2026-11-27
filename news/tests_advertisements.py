from datetime import timedelta

from django.contrib import admin
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Advertisement


class AdvertisementPlacementTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.current_ad = Advertisement.objects.create(
            title="Current header campaign",
            image="advertisements/header.jpg",
            target_url="https://advertiser.example/",
            placement=Advertisement.Placement.HEADER,
            starts_at=self.now - timedelta(days=1),
            ends_at=self.now + timedelta(days=1),
        )

    def render_slot(self, placement):
        template = Template('{% load advertisements %}{% advertisement_slot placement %}')
        return template.render(Context({"placement": placement}))

    def test_slot_renders_only_active_in_date_range_ads_for_its_placement(self):
        Advertisement.objects.create(
            title="Inactive campaign", image="ads/inactive.jpg",
            target_url="https://advertiser.example/", placement="header", is_active=False,
        )
        Advertisement.objects.create(
            title="Future campaign", image="ads/future.jpg",
            target_url="https://advertiser.example/", placement="header",
            starts_at=self.now + timedelta(days=1),
        )
        Advertisement.objects.create(
            title="Article campaign", image="ads/article.jpg",
            target_url="https://advertiser.example/", placement="article",
        )

        rendered = self.render_slot("header")

        self.assertIn("Current header campaign", rendered)
        self.assertNotIn("Inactive campaign", rendered)
        self.assertNotIn("Future campaign", rendered)
        self.assertNotIn("Article campaign", rendered)

    def test_empty_placement_renders_no_ad_markup(self):
        rendered = self.render_slot("sidebar")
        self.assertNotIn("managed-advertisement", rendered)
        self.assertNotIn("<ins", rendered)

    def test_banner_uses_image_and_target_url(self):
        rendered = self.render_slot("header")
        self.assertIn(self.current_ad.image.url, rendered)
        self.assertIn(self.current_ad.target_url, rendered)

    def test_adsense_requires_both_client_and_placement_slot(self):
        with override_settings(ADSENSE_CLIENT_ID="ca-pub-example", ADSENSE_SLOT_IDS={"header": "123"}):
            rendered = self.render_slot("header")
        self.assertIn('data-ad-client="ca-pub-example"', rendered)
        self.assertIn('data-ad-slot="123"', rendered)

    def test_advertisement_is_registered_in_admin(self):
        self.assertIn(Advertisement, admin.site._registry)

    def test_homepage_renders_homepage_placement(self):
        Advertisement.objects.create(
            title="Homepage campaign", image="ads/homepage.jpg",
            target_url="https://advertiser.example/", placement="homepage",
        )

        response = self.client.get("/")

        self.assertContains(response, "Homepage campaign")
