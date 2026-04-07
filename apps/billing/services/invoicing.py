from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.billing.models import Invoice, Subscription


@transaction.atomic
def ensure_pending_invoice_for_subscription(sub: Subscription) -> Invoice | None:
    """
    MVP: cria fatura 'pending' com vencimento no fim do trial (ou hoje se não houver trial).
    Não cria fatura para planos gratuitos.
    """

    price: Decimal = sub.plan.price
    if price is None or price == 0:
        return None

    due = sub.trial_end_date or sub.start_date
    inv, _ = Invoice.objects.get_or_create(
        company_id=sub.company_id,
        subscription_id=sub.pk,
        status=Invoice.Status.PENDING,
        due_date=due,
        defaults={"amount": price},
    )
    # mantém amount coerente com o plano atual
    if inv.amount != price:
        inv.amount = price
        inv.save(update_fields=["amount"])
    return inv

