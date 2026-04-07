from __future__ import annotations

from django.contrib.auth.views import LoginView
from django.urls import reverse


class DashboardFirstLoginView(LoginView):
    """Sempre redireciona para o dashboard após login (ignora `next`)."""

    def get_success_url(self):
        return reverse("dashboard")

