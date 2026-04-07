class TenantMiddleware:
    """Anexa `request.company` a partir do usuário autenticado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            request.company = getattr(user, "company", None)
        return self.get_response(request)
