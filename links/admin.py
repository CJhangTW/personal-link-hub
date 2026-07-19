from django.contrib import admin

from .models import LinkItem, SiteProfile


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "hero_title", "is_published", "updated_at")
    fieldsets = (
        ("Brand", {"fields": ("display_name", "logo_url", "hero_title", "hero_subtitle")} ),
        ("About", {"fields": ("intro_text", "location_text", "is_published")} ),
        ("Metadata", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists() and super().has_add_permission(request)


@admin.register(LinkItem)
class LinkItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "is_visible",
        "display_order",
        "click_count",
        "last_clicked_at",
    )
    list_editable = ("is_visible", "display_order")
    list_filter = ("is_visible",)
    search_fields = ("title", "description", "slug", "target_url")
    ordering = ("display_order", "title")
    readonly_fields = ("click_count", "last_clicked_at", "created_at", "updated_at")
