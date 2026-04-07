from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.billing.models import Module, Plan, PlanFeature


class Command(BaseCommand):
    help = "Cria/atualiza módulos, planos e features (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        guarantees, _ = Module.objects.get_or_create(
            key="guarantees",
            defaults={
                "name": "Garantias",
                "description": "Módulo de garantias rurais (matrículas, áreas, safras, PDF).",
                "is_active": True,
            },
        )

        def upsert_plan(*, name: str, price: Decimal, billing_type: str, description: str) -> Plan:
            p, created = Plan.objects.get_or_create(
                module=guarantees,
                name=name,
                defaults={
                    "price": price,
                    "billing_type": billing_type,
                    "description": description,
                    "is_active": True,
                },
            )
            if not created:
                dirty = False
                if p.price != price:
                    p.price = price
                    dirty = True
                if p.billing_type != billing_type:
                    p.billing_type = billing_type
                    dirty = True
                if p.description != description:
                    p.description = description
                    dirty = True
                if not p.is_active:
                    p.is_active = True
                    dirty = True
                if dirty:
                    p.save(update_fields=["price", "billing_type", "description", "is_active"])
            return p

        def set_features(plan: Plan, feats: dict) -> None:
            for k, v in feats.items():
                PlanFeature.objects.update_or_create(plan=plan, key=k, defaults={"value": v})

        free = upsert_plan(
            name="Grátis",
            price=Decimal("0.00"),
            billing_type=Plan.BillingType.MONTHLY,
            description="Para conhecer o sistema e começar com o básico.",
        )
        set_features(
            free,
            {
                "limits.max_properties": 1,
                "limits.max_areas": 1,
                "limits.max_guarantees": 1,
                "limits.max_crop_seasons": 1,
                "capabilities.can_print": False,
            },
        )

        per_unit = upsert_plan(
            name="Por Matrícula",
            price=Decimal("400.00"),
            billing_type=Plan.BillingType.PER_UNIT,
            description="Cobrança por matrícula (unidade).",
        )
        set_features(
            per_unit,
            {
                "limits.max_areas": 1,
                "capabilities.can_print": True,
                "rules.one_guarantee_per_crop_season": True,
                "rules.lock_on_first_print": True,
                "rules.immutable_after_lock": True,
            },
        )

        yearly = upsert_plan(
            name="Anual",
            price=Decimal("2400.00"),
            billing_type=Plan.BillingType.YEARLY,
            description="Plano anual com registros ilimitados.",
        )
        set_features(
            yearly,
            {
                "capabilities.can_print": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed concluído: módulo Garantias e planos criados/atualizados."))

