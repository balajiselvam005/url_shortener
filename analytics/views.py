from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from shortener.models import ShortURL

@login_required
def dashboard(request):
    urls = ShortURL.objects.filter(created_by=request.user)

    return render(request, "dashboard.html", {"urls": urls})