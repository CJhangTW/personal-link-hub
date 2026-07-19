from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


def validate_http_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Enter a valid URL starting with http:// or https://.")


slug_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message="Use lowercase letters, numbers, and single hyphens only.",
)


class SiteProfile(models.Model):
    display_name = models.CharField(max_length=120, default="My Links")
    logo_url = models.URLField(max_length=2048, blank=True, validators=[validate_http_url])
    hero_title = models.CharField(max_length=160, default="My Links")
    hero_subtitle = models.CharField(max_length=240, default="A personal link hub")
    intro_text = models.TextField(
        default="Projects, writing, and useful places online.",
    )
    location_text = models.CharField(max_length=80, blank=True, default="")
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "site profile"
        verbose_name_plural = "site profile"

    def clean(self):
        if not self.pk and SiteProfile.objects.exists():
            raise ValidationError("Only one site profile can be configured.")

    @classmethod
    def get_current(cls):
        return cls.objects.filter(is_published=True).first()

    def __str__(self):
        return self.display_name


class LinkItem(models.Model):
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True, default="")
    slug = models.CharField(max_length=80, unique=True, validators=[slug_validator])
    target_url = models.URLField(max_length=2048, validators=[validate_http_url])
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    click_count = models.PositiveBigIntegerField(default=0, editable=False)
    last_clicked_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "title"]
        indexes = [models.Index(fields=["is_visible", "display_order"])]

    def __str__(self):
        return f"{self.title} ({self.slug})"
