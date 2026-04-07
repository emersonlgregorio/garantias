from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from apps.billing.models import Module, PlanFeature, Subscription


@dataclass(frozen=True)
class Entitlements:
    features: dict[str, object]

    def get_bool(self, key: str, default: bool = False) -> bool:
        v = self.features.get(key, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "sim")
        return default

    def get_int(self, key: str, default: int | None = None) -> int | None:
        v = self.features.get(key, default)
        if v is None:
            return None
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            try:
                return int(v.strip())
            except ValueError:
                return default
        return default


def get_company_subscription(*, company_id: int, module_key: str) -> Subscription | None:
    return (
        Subscription.objects.select_related("module", "plan", "plan__module")
        .filter(company_id=company_id, module__key=module_key)
        .first()
    )


def is_subscription_access_ok(sub: Subscription | None) -> bool:
    if sub is None:
        return False
    if sub.status == Subscription.Status.ACTIVE:
        return True
    if sub.status == Subscription.Status.TRIAL:
        if not sub.trial_end_date:
            return False
        return sub.trial_end_date >= timezone.localdate()
    return False


def get_entitlements(sub: Subscription) -> Entitlements:
    feats = PlanFeature.objects.filter(plan_id=sub.plan_id).values_list("key", "value")
    return Entitlements(features={k: v for (k, v) in feats})


def ensure_module_access(*, company_id: int, module_key: str) -> Subscription:
    sub = get_company_subscription(company_id=company_id, module_key=module_key)
    if not is_subscription_access_ok(sub):
        raise PermissionError("Assinatura inexistente, expirada ou sem pagamento.")
    return sub


def can_print(sub: Subscription) -> bool:
    ent = get_entitlements(sub)
    return ent.get_bool("capabilities.can_print", default=False)


def should_lock_on_first_print(sub: Subscription) -> bool:
    ent = get_entitlements(sub)
    return ent.get_bool("rules.lock_on_first_print", default=False)


def get_limit(sub: Subscription, key: str) -> int | None:
    """Retorna limite inteiro (None => ilimitado / não configurado)."""
    ent = get_entitlements(sub)
    return ent.get_int(key, default=None)

