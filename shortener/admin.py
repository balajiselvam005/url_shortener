from django.contrib import admin
from .models import ShortURL


@admin.action(description="Deactivate Selected URLs")
def deactivate_urls(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.action(description="Activate Selected URLs")
def deactivate_urls(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "original_url",
        "click_count",
        "is_active",
        "created_by",
        "created_at"
    )

    list_filter = ("is_active", "created_at")
    search_fields = ("short_code", "original_url")
    actions = [deactivate_urls]
