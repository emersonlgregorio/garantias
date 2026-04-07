from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.billing.models import Plan, Subscription
from apps.billing.serializers import PlanSerializer, SubscriptionSerializer
from apps.core.mixins import CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, HasCompanyContext, IsCompanyAdmin


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by("name")
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]


class SubscriptionViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany, IsCompanyAdmin]
    queryset = Subscription.objects.select_related("company", "plan").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [HasCompanyContext(), BelongsToUserCompany()]
        return [HasCompanyContext(), BelongsToUserCompany(), IsCompanyAdmin()]
