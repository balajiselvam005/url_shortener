import csv
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from shortener.models import ShortURL
from analytics.models import Click

from django.utils.timezone import timedelta, now
from django.db.models.functions import TruncDay
from django.db.models import Count


# dashboard and analytics are protected views
# public routes are handled via middleware
# Decorator is preferred here since most app URLs are public.
@login_required
def dashboard(request):
    if request.method == "POST":
        ids = request.POST.getlist("selected_urls")
        if ids:
            ShortURL.objects.filter(id__in=ids, created_by=request.user).delete()

    urls = ShortURL.objects.filter(created_by=request.user)

    return render(request, "dashboard.html", {"urls": urls})

@login_required
def analytics_view(request, code):
    url = get_object_or_404(ShortURL, short_code=code, created_by=request.user)
    
    total_clicks = url.click_count

    last_30_days = now() - timedelta(days=30)

    clicks_per_day = (
        Click.objects
        .filter(short_url=url, clicked_at__gte=last_30_days)
        .annotate(day=TruncDay('clicked_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    top_referers = (
        Click.objects
        .filter(short_url=url)
        .values('referer')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    recent_clicks = (
        Click.objects
        .filter(short_url=url)
        .order_by('-clicked_at')[:10]
    )

    return render(request, "analytics.html", {
        "url": url,
        "total_clicks": total_clicks,
        "clicks_per_day": json.dumps(list(clicks_per_day), default=str),
        "top_referers": json.dumps(list(top_referers)),
        "recent_clicks": recent_clicks
    })


@login_required
def bulk_import(request):
    results = []

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            return render(request, "bulk_import.html", {"error": "No file uploaded"})

        if not csv_file.name.endswith(".csv"):
            return render(request, "bulk_import.html", {"error": "File must be a .csv"})

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            original_url = row.get("url", "").strip()
            custom_alias = row.get("custom_alias", "").strip()
            expires_in_days = row.get("expires_in_days", "").strip()

            if not original_url:
                results.append({"url": "—", "status": "Skipped — no URL"})
                continue

            expires_at = None
            if expires_in_days:
                try:
                    expires_at = now() + timedelta(days=int(expires_in_days))
                except ValueError:
                    results.append({"url": original_url, "status": "Skipped — invalid expiry value"})
                    continue

            if custom_alias:
                if ShortURL.objects.filter(short_code=custom_alias).exists():
                    results.append({"url": original_url, "status": f"Alias '{custom_alias}' already taken"})
                    continue

            try:
                obj = ShortURL.objects.create(
                    original_url=original_url,
                    custom_alias=custom_alias if custom_alias else None,
                    expires_at=expires_at,
                    created_by=request.user,
                    ip_address=request.META.get("REMOTE_ADDR")
                )
                results.append({
                    "url": original_url,
                    "status": f"Created: /s/{obj.short_code}/"
                })

            except Exception as e:
                results.append({"url": original_url, "status": f"Error — {str(e)}"})

    return render(request, "bulk_import.html", {"results": results})