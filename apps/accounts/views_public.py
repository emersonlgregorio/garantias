from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from apps.accounts.forms import PublicSignupForm


class LandingView(TemplateView):
    template_name = "landing/index.html"


class PublicSignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = PublicSignupForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Conta criada com sucesso. Faça login com seu e-mail e senha para continuar.",
        )
        return super().form_valid(self)
