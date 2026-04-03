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
    if path.startswith('/static/'):
        return True
    return path in EXEMPT_URLS

class LoginRequiredMiddleware:
    """
    Middleware to require login for most routes.
    Public routes like home, shorten API, and redirects are excluded.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not is_exempt(request.path):
            return redirect(f'/login/?next={request.path}')
        return self.get_response(request)