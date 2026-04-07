from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class HasCompanyContext(BasePermission):
    """Exige usuário autenticado com empresa (superusuário sem empresa só para /admin)."""

    message = "Usuário sem empresa vinculada."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "company_id", None) is not None


class IsCompanyAdmin(BasePermission):
    message = "Apenas administradores da empresa."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == User.Role.ADMIN


class BelongsToUserCompany(BasePermission):
    """Objeto com `company` direto."""

    message = "Recurso de outra empresa."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        oc = getattr(obj, "company", None)
        if oc is None:
            return False
        return oc.pk == user.company_id


class BelongsToUserCompanyViaProperty(BasePermission):
    """Objeto com `property` -> `company`."""

    message = "Recurso de outra empresa."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        prop = getattr(obj, "property", None)
        if prop is None:
            return False
        return prop.company_id == user.company_id


class SameCompanyUser(BasePermission):
    """Usuário-alvo pertence à mesma empresa do solicitante."""

    message = "Usuário de outra empresa."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        if getattr(user, "company_id", None) is None:
            return False
        return obj.company_id == user.company_id


class BelongsToUserCompanyViaGuarantee(BasePermission):
    """Objeto com `guarantee` -> `company`."""

    message = "Recurso de outra empresa."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        g = getattr(obj, "guarantee", None)
        if g is None:
            return False
        return g.company_id == user.company_id
