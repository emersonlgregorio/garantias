from django.views.generic import TemplateView

from apps.accounts.views_signup_wizard import SignupWizardView


class LandingView(TemplateView):
    template_name = "landing/index.html"


class PublicSignupView(SignupWizardView):
    pass
