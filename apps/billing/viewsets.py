from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.billing.models import Invoice, Plan, Subscription
from apps.billing.serializers import InvoiceSerializer, PlanSerializer, SubscriptionSerializer
from apps.core.mixins import CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, HasCompanyContext, IsCompanyAdmin


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Plan.objects.select_related("module")
        .prefetch_related("features")
        .filter(is_active=True, module__is_active=True)
        .order_by("module__name", "price")
    )
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]


class SubscriptionViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany, IsCompanyAdmin]
    queryset = Subscription.objects.select_related("company", "module", "plan", "plan__module").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [HasCompanyContext(), BelongsToUserCompany()]
        return [HasCompanyContext(), BelongsToUserCompany(), IsCompanyAdmin()]


class InvoiceViewSet(CompanyScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany, IsCompanyAdmin]
    queryset = Invoice.objects.select_related(
        "company",
        "subscription",
        "subscription__module",
        "subscription__plan",
        "subscription__plan__module",
    ).all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())
