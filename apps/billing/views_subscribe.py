from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Module, Plan, Subscription
from apps.billing.services.invoicing import ensure_pending_invoice_for_subscription


class SubscribeSerializer(serializers.Serializer):
    module_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()


class SubscribeView(APIView):
    """
    POST /api/v1/subscribe
    - cria/atualiza Subscription da empresa em trial (7 dias)
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        ser = SubscribeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        module = Module.objects.filter(pk=ser.validated_data["module_id"], is_active=True).first()
        if not module:
            return Response({"detail": "Módulo inválido."}, status=400)
        plan = Plan.objects.filter(pk=ser.validated_data["plan_id"], module_id=module.pk, is_active=True).first()
        if not plan:
            return Response({"detail": "Plano inválido para este módulo."}, status=400)

        company = getattr(request.user, "company", None)
        if not company:
            return Response({"detail": "Usuário sem empresa vinculada."}, status=403)

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
                "is_locked": False,
                "lock_reason": "",
                "locked_at": None,
            },
        )

        # Se já existe, reinicia para trial do plano escolhido (MVP).
        sub.plan = plan
        sub.status = Subscription.Status.TRIAL
        sub.trial_end_date = trial_end
        sub.end_date = None
        sub.save(update_fields=["plan", "status", "trial_end_date", "end_date"])
        ensure_pending_invoice_for_subscription(sub)

        return Response(
            {
                "id": sub.pk,
                "company_id": company.pk,
                "module_id": module.pk,
                "plan_id": plan.pk,
                "status": sub.status,
                "trial_end_date": sub.trial_end_date,
            },
            status=201,
        )

