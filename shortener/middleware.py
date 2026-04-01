from django.shortcuts import redirect

EXEMPT_URLS = [
    '/',
    '/login/',
    '/api/shorten/',
]

def is_exempt(path):
    if path.startswith('/s/'):
        return True
    if path.startswith('/qr/'):
        return True
    return path in EXEMPT_URLS

class LoginRequiredMiddleware:
    """
    Middleware alternative to @login_required decorator.
    Protects all views globally except whitelisted public URLs.
    Unlike @login_required which is applied per-view, this middleware
    enforces auth at the request level before any view is called.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not is_exempt(request.path):
            return redirect(f'/login/?next={request.path}')
        return self.get_response(request)