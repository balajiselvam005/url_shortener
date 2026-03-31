from django.contrib import admin
from .models import Click

@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ("short_url", "clicked_at", "ip_address")
    list_filter = ("clicked_at", "short_url")
    readonly_fields = [field.name for field in Click._meta.fields]
