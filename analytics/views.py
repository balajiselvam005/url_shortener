from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from shortener.models import ShortURL

@login_required
def dashboard(request):
    if request.method == "POST":
        ids = request.POST.getlist("selected_urls")
        ShortURL.objects.filter(id__in=ids, created_by=request.user).delete()

    urls = ShortURL.objects.filter(created_by=request.user)

    return render(request, "dashboard.html", {"urls": urls})