from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.response import Response

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
