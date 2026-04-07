from rest_framework import viewsets

from apps.core.mixins import CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, HasCompanyContext
from apps.masterdata.models import BusinessPartner, Currency, ProductionProduct
from apps.masterdata.serializers import (
    BusinessPartnerSerializer,
    CurrencySerializer,
    ProductionProductSerializer,
)


class BusinessPartnerViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = BusinessPartnerSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = BusinessPartner.objects.select_related("company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class ProductionProductViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ProductionProductSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = ProductionProduct.objects.select_related("company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class CurrencyViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CurrencySerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = Currency.objects.select_related("company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

