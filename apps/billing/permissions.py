from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.billing.services.entitlements import ensure_module_access


class HasModuleAccess(BasePermission):
    """Permite acesso ao módulo se assinatura ativa ou trial válido."""

    message = "Acesso ao módulo bloqueado (trial expirado ou assinatura inativa)."

    def __init__(self, module_key: str):
        self.module_key = module_key

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        cid = getattr(user, "company_id", None)
        if cid is None:
            return False
        try:
            ensure_module_access(company_id=cid, module_key=self.module_key)
            return True
        except PermissionError:
            return False

