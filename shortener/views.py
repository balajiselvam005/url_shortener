from django.shortcuts import render
from .models import ShortURL

def home(request):
    short_url = None
    if request.method == "POST":
        original_url = request.POST.get("url")
        obj = ShortURL.objects.create(original_url=original_url)
        short_url = request.build_absolute_uri(f"/s/{obj.short_code}/")
    return render(request, "home.html", {"short_url": short_url})