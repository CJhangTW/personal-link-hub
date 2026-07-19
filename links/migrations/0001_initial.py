from django.db import migrations, models

import links.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LinkItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, default="", max_length=240)),
                ("slug", models.CharField(max_length=80, unique=True, validators=[links.models.slug_validator])),
                ("target_url", models.URLField(max_length=2048, validators=[links.models.validate_http_url])),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_visible", models.BooleanField(default=True)),
                ("click_count", models.PositiveBigIntegerField(default=0, editable=False)),
                ("last_clicked_at", models.DateTimeField(blank=True, editable=False, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["display_order", "title"],
                "indexes": [models.Index(fields=["is_visible", "display_order"], name="links_linkit_is_vis_1b17d3_idx")],
            },
        ),
        migrations.CreateModel(
            name="SiteProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(default="My Links", max_length=120)),
                ("logo_url", models.URLField(blank=True, max_length=2048, validators=[links.models.validate_http_url])),
                ("hero_title", models.CharField(default="My Links", max_length=160)),
                ("hero_subtitle", models.CharField(default="A personal link hub", max_length=240)),
                ("intro_text", models.TextField(default="Projects, writing, and useful places online.")),
                ("location_text", models.CharField(blank=True, default="", max_length=80)),
                ("is_published", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "site profile", "verbose_name_plural": "site profile"},
        ),
    ]
