from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.billing.services.entitlements import ensure_module_access, get_limit
from apps.core.mixins import CompanyScopedPropertyQuerysetMixin, CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, BelongsToUserCompanyViaProperty, HasCompanyContext
from apps.properties.models import Area, Property
from apps.properties.serializers import AreaSerializer, PropertySerializer


class PropertyViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = Property.objects.select_related("company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())


class AreaViewSet(CompanyScopedPropertyQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AreaSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompanyViaProperty]
    queryset = Area.objects.select_related("property", "property__company").all()

    def get_queryset(self):
        qs = self.scope_queryset(super().get_queryset())
        qs = qs.annotate(linked_guarantee_count=Count("guarantees", distinct=True))
        pid = self.request.query_params.get("property")
        if pid:
            qs = qs.filter(property_id=pid)
        return qs

    def create(self, request, *args, **kwargs):
        # Limite por plano (módulo Garantias): número máximo de matrículas (areas)
        user = request.user
        if not user.is_superuser:
            cid = getattr(user, "company_id", None)
            if cid is not None:
                try:
                    sub = ensure_module_access(company_id=cid, module_key="guarantees")
                    lim = get_limit(sub, "limits.max_areas")
                    if lim is not None:
                        current = Area.objects.filter(property__company_id=cid).count()
                        if current >= lim:
                            return Response(
                                {"detail": "Limite do plano atingido: não é possível cadastrar mais matrículas."},
                                status=status.HTTP_409_CONFLICT,
                            )
                except PermissionError:
                    return Response(
                        {"detail": "Acesso bloqueado: assinatura inativa ou trial expirado."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.guarantees.exists():
            return Response(
                {
                    "detail": "Não é possível excluir: existe garantia vinculada a esta área (matrícula). "
                    "Remova o vínculo na garantia antes de excluir."
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)
