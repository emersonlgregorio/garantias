from rest_framework import viewsets

from apps.core.mixins import CompanyScopedGuaranteeQuerysetMixin, CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, BelongsToUserCompanyViaGuarantee, HasCompanyContext
from apps.crops.models import Commitment, CropSeason
from apps.crops.serializers import CommitmentSerializer, CropSeasonSerializer


class CropSeasonViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CropSeasonSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = CropSeason.objects.select_related("company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())


class CommitmentViewSet(CompanyScopedGuaranteeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CommitmentSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompanyViaGuarantee]
    queryset = Commitment.objects.select_related("guarantee", "crop_season", "guarantee__company").all()

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())
