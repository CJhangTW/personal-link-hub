from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .models import LinkItem, SiteProfile


class SiteProfileModelTests(TestCase):
    def test_profile_can_store_admin_editable_brand_content(self):
        profile = SiteProfile.objects.create(
            display_name="Cheng Jhang",
            logo_url="https://example.com/logo.svg",
            hero_title="My Links",
            hero_subtitle="A personal link hub",
            intro_text="Projects, writing, and useful places online.",
            location_text="Taiwan",
        )

        self.assertEqual(str(profile), "Cheng Jhang")
        self.assertEqual(SiteProfile.objects.count(), 1)


class LinkItemModelTests(TestCase):
    def test_link_item_rejects_non_http_target_url(self):
        link = LinkItem(
            title="Invalid",
            description="Not a web link",
            slug="invalid",
            target_url="javascript:alert(1)",
        )

        with self.assertRaisesMessage(Exception, "Enter a valid URL"):
            link.full_clean()

    def test_link_item_slug_is_unique(self):
        LinkItem.objects.create(title="Portfolio", slug="portfolio", target_url="https://example.com")
        duplicate = LinkItem(title="Another", slug="portfolio", target_url="https://example.org")

        with self.assertRaises(Exception):
            duplicate.full_clean()


class HomePageTests(TestCase):
    def setUp(self):
        SiteProfile.objects.create(
            display_name="Cheng Jhang",
            hero_title="My Links",
            hero_subtitle="A personal link hub",
            intro_text="Projects and writing.",
            location_text="Taiwan",
        )

    def test_homepage_renders_profile_and_visible_links_in_order(self):
        LinkItem.objects.create(
            title="Second",
            description="Second link",
            slug="second",
            target_url="https://example.com/second",
            display_order=2,
        )
        LinkItem.objects.create(
            title="Hidden",
            description="Hidden link",
            slug="hidden",
            target_url="https://example.com/hidden",
            display_order=1,
            is_visible=False,
        )
        LinkItem.objects.create(
            title="First",
            description="First link",
            slug="first",
            target_url="https://example.com/first",
            display_order=0,
        )

        response = self.client.get(reverse("links:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Links")
        self.assertContains(response, "First")
        self.assertContains(response, "/r/first/")
        self.assertNotContains(response, "Hidden")
        self.assertLess(response.content.index(b"First"), response.content.index(b"Second"))

    def test_healthcheck_returns_ok_without_database_work(self):
        response = self.client.get(reverse("links:healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")


class RedirectTests(TestCase):
    def test_active_link_returns_302_and_updates_aggregate_metrics(self):
        link = LinkItem.objects.create(
            title="Portfolio",
            slug="portfolio",
            target_url="https://example.com/portfolio",
        )

        response = self.client.get(reverse("links:redirect-link", kwargs={"slug": "portfolio"}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com/portfolio")
        link.refresh_from_db()
        self.assertEqual(link.click_count, 1)
        self.assertIsNotNone(link.last_clicked_at)

    def test_missing_or_hidden_link_returns_404(self):
        LinkItem.objects.create(
            title="Hidden",
            slug="hidden",
            target_url="https://example.com/hidden",
            is_visible=False,
        )

        self.assertEqual(
            self.client.get(reverse("links:redirect-link", kwargs={"slug": "missing"})).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(reverse("links:redirect-link", kwargs={"slug": "hidden"})).status_code,
            404,
        )


class AdminAccessTests(TestCase):
    def test_admin_requires_login(self):
        response = self.client.get("/admin/links/linkitem/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])


class ContainerConfigurationTests(TestCase):
    def test_compose_runtime_does_not_require_uv_cache(self):
        compose = (Path(settings.BASE_DIR) / "compose.yaml").read_text(encoding="utf-8")

        self.assertNotIn("uv run", compose)
        self.assertIn("gunicorn config.wsgi:application", compose)

    def test_dockerfile_does_not_require_buildkit_cache_mount(self):
        dockerfile = (Path(settings.BASE_DIR) / "Dockerfile").read_text(encoding="utf-8")

        self.assertNotIn("--mount=type=cache", dockerfile)
