from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseGone
from django.db.models import F
from analytics.models import Click
from .models import ShortURL

def home(request):
    short_url = None
    if request.method == "POST":
        original_url = request.POST.get("url")
        obj = ShortURL.objects.create(original_url=original_url, created_by=request.user if request.user.is_authenticated else None)
        short_url = request.build_absolute_uri(f"/s/{obj.short_code}/")
    return render(request, "home.html", {"short_url": short_url})

def redirect_view(request, code):
    obj = get_object_or_404(ShortURL, short_code=code)

    if not obj.is_active:
        return HttpResponseGone("The link is inactive")
    
    if obj.expires_at and obj.expires_at < timezone.now():
        return HttpResponseGone("The link has expired")
    
    ShortURL.objects.filter(id=obj.id).update(click_count=F('click_count') + 1)

    Click.objects.create(
        short_url = obj,
        ip_address = request.META.get("REMOTE_ADDR"),
        user_agent = request.META.get("HTTP_USER_AGENT"),
        referer = request.META.get("HTTP_REFERER"),
        country = "India"
    )

    return redirect(obj.original_url)

@login_required
def toggle_url(request, id):
    obj = get_object_or_404(ShortURL, id=id, created_by=request.user)
    
    obj.is_active = not obj.is_active
    obj.save()

    return redirect("/dashboard/")