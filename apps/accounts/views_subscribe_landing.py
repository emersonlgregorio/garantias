from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View

from apps.billing.models import Module, Plan, Subscription
from apps.billing.services.invoicing import ensure_pending_invoice_for_subscription


class SubscribeLandingView(LoginRequiredMixin, View):
    """Form POST da landing → cria Subscription em trial e redireciona para o app."""

    @transaction.atomic
    def post(self, request):
        module_id = request.POST.get("module_id")
        plan_id = request.POST.get("plan_id")
        if not module_id or not plan_id:
            messages.error(request, "Selecione um plano válido.")
            return redirect("landing_pricing")

        module = Module.objects.filter(pk=module_id, is_active=True).first()
        plan = Plan.objects.filter(pk=plan_id, module_id=module_id, is_active=True).first()
        if not module or not plan:
            messages.error(request, "Plano ou módulo inválido.")
            return redirect("landing_pricing")

        company = getattr(request.user, "company", None)
        if not company:
            messages.error(request, "Usuário sem empresa vinculada.")
            return redirect("landing_pricing")

        today = timezone.localdate()
        trial_end = today + timedelta(days=7)

        sub, _ = Subscription.objects.select_for_update().get_or_create(
            company_id=company.pk,
            module_id=module.pk,
            defaults={
                "plan": plan,
                "status": Subscription.Status.TRIAL,
                "trial_end_date": trial_end,
                "start_date": today,
                "end_date": None,
            },
        )
        sub.plan = plan
        sub.status = Subscription.Status.TRIAL
        sub.trial_end_date = trial_end
        sub.end_date = None
        sub.save(update_fields=["plan", "status", "trial_end_date", "end_date"])
        ensure_pending_invoice_for_subscription(sub)

        messages.success(request, "Trial iniciado. Você já pode usar o módulo.")
        return redirect("dashboard")

