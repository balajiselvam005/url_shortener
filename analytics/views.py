import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from shortener.models import ShortURL
from analytics.models import Click

from django.utils.timezone import timedelta, now
from django.db.models.functions import TruncDay
from django.db.models import Count

@login_required
def dashboard(request):
    if request.method == "POST":
        ids = request.POST.getlist("selected_urls")
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