from __future__ import annotations

from django.views.generic import TemplateView

from apps.billing.models import Module


class PricingView(TemplateView):
    template_name = "landing/pricing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        modules = list(
            Module.objects.filter(is_active=True)
            .prefetch_related("plans", "plans__features")
            .order_by("name")
        )
        # Mantém apenas planos ativos.
        for m in modules:
            m.active_plans = [p for p in m.plans.all() if p.is_active]
        ctx["modules"] = modules
        return ctx

