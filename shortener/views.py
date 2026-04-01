import json
import qrcode
import logging

from shortener.forms import ShortenForm
from shortener.serializers import ShortenSerializer
logger = logging.getLogger(__name__)

from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, timedelta
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseGone
from django.db.models import F, Q
from analytics.models import Click
from .models import ShortURL, generate_code

def home(request):
    short_url = None
    form = ShortenForm()
    
    if request.method == "POST":
        form = ShortenForm(request.POST)
        if form.is_valid():
            original_url = form.cleaned_data["url"]
            custom_alias = form.cleaned_data.get("custom_alias")

            ip = request.META.get("REMOTE_ADDR")
            obj = ShortURL.objects.create(
                ip_address = ip,
                original_url = original_url,
                custom_alias = custom_alias,
                created_by = request.user if request.user.is_authenticated else None
            )
            short_url = request.build_absolute_uri(f"/s/{obj.short_code}")

    return render(request, "home.html", {"form": form, "short_url": short_url})

def redirect_view(request, code):
    obj = get_object_or_404(ShortURL, short_code=code)

    if not obj.is_active:
        return Http404("The link is inactive")
    
    if obj.expires_at and obj.expires_at < timezone.now():
        return HttpResponseGone("The link has expired")
    
    try:
    
        ShortURL.objects.filter(id=obj.id).update(click_count=F('click_count') + 1)

        Click.objects.create(
            short_url = obj,
            ip_address = request.META.get("REMOTE_ADDR"),
            user_agent = request.META.get("HTTP_USER_AGENT"),
            referer = request.META.get("HTTP_REFERER") or "",
            country = "India"
        )
    
    except Exception as e :
        logger.error(f"Click logging failed for {code} : {e}")

    return HttpResponseRedirect(obj.original_url)

def generate_qr(request, code):
    try:
        obj = get_object_or_404(ShortURL, short_code=code)
        url = request.build_absolute_uri(f"/s/{obj.short_code}")
        qr = qrcode.make(url)
        response = HttpResponse(content_type="image/png")
        qr.save(response, "PNG")
        return response
    
    except Exception:
        return HttpResponse("QR generation failed", status=500)

@csrf_exempt
def api_shorten(request):

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    ip = request.META.get("REMOTE_ADDR")
    last_hour = now() - timedelta(hours=1)
    count = ShortURL.objects.filter(ip_address=ip , created_at__gte=last_hour).count()
    if count >= 10:
        return JsonResponse({"error": "Rate Limit Exceeded"}, status=429)
    
    serializer = ShortenSerializer(data = data)
    if not serializer.is_valid():
        return JsonResponse({"error": serializer.errors}, status=400)
    
    validated = serializer.validated_data
    url = validated["url"]
    custom_alias = validated.get("custom_alias", "")
    expires_days = validated.get("expires_in_days")

    expires_at = None

    if expires_days:
        expires_at = now() + timedelta(days=expires_days)   

    obj = ShortURL.objects.create(  
        ip_address=ip,
        original_url=url,
        custom_alias=custom_alias if custom_alias else None,
        expires_at=expires_at
    )

    return JsonResponse({
        "short_url": request.build_absolute_uri(f"/s/{obj.short_code}/"),
        "short_code": obj.short_code,
        "expires_at": str(obj.expires_at)
    })


@login_required
def toggle_url(request, id):
    obj = get_object_or_404(ShortURL, id=id, created_by=request.user)
    
    obj.is_active = not obj.is_active
    obj.save()

    return redirect("/dashboard/")