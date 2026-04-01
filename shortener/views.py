import json
import qrcode

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, timedelta
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import F, Q
from analytics.models import Click
from .models import ShortURL, generate_code

def home(request):
    short_url = None
    error = None
    
    if request.method == "POST":
        try:
            original_url = request.POST.get("url")
            custom_alias = request.POST.get("custom_alias")

            if not original_url:
                error = "URL is required"

            elif custom_alias and ShortURL.objects.filter(short_code=custom_alias).exists():
                error = "Custom alias already exists"

            else:
                ip = request.META.get("REMOTE_ADDR")
                obj = ShortURL.objects.create(ip_address=ip, original_url=original_url, short_code=custom_alias if custom_alias else None, created_by=request.user if request.user.is_authenticated else None)
            
                short_url = request.build_absolute_uri(f"/s/{obj.short_code}/")

        except Exception as e:
            error = "Something went wrong"

    return render(request, "home.html", {"short_url": short_url, "error": error})

def redirect_view(request, code):
    obj = get_object_or_404(ShortURL, Q(short_code=code) | Q(custom_alias=code))

    if not obj.is_active:
        return Http404("The link is inactive")
    
    if obj.expires_at and obj.expires_at < timezone.now():
        return Http404("The link has expired")
    
    try:
    
        ShortURL.objects.filter(id=obj.id).update(click_count=F('click_count') + 1)

        Click.objects.create(
            short_url = obj,
            ip_address = request.META.get("REMOTE_ADDR"),
            user_agent = request.META.get("HTTP_USER_AGENT"),
            referer = request.META.get("HTTP_REFERER") or "",
            country = "India"
        )
    
    except:
        pass

    return redirect(obj.original_url)

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
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    ip = request.META.get("REMOTE_ADDR")
    last_hour = now() - timedelta(hours=1)
    count = ShortURL.objects.filter(ip_address=ip , created_at__gte=last_hour).count()
    if count >= 10:
        return JsonResponse({"error": "Rate Limit Exceeded"}, status=429)

    url = data.get("url")
    custom_alias = data.get("custom_alias")
    expires_days = data.get("expires_in_days")

    if not url:
        return JsonResponse({"error": "URL required"}, status=400)

    if custom_alias:
        if ShortURL.objects.filter(short_code=custom_alias).exists():
            return JsonResponse({"error": "Alias exists"}, status=400)
        code = custom_alias
    else:
        code = generate_code()

    expires_at = None
    if expires_days:
        expires_at = now() + timedelta(days=int(expires_days))

    obj = ShortURL.objects.create(  
        ip_address=ip,
        original_url=url,
        short_code=code,
        expires_at=expires_at
    )

    return JsonResponse({
        "short_url": f"http://127.0.0.1:8000/s/{obj.short_code}/",
        "short_code": obj.short_code,
        "expires_at": str(obj.expires_at)
    })


@login_required
def toggle_url(request, id):
    obj = get_object_or_404(ShortURL, id=id, created_by=request.user)
    
    obj.is_active = not obj.is_active
    obj.save()

    return redirect("/dashboard/")