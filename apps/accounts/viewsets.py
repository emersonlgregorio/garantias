from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets

from apps.accounts.models import Company, User
from apps.accounts.serializers import CompanySerializer, UserSerializer
from apps.core.permissions import HasCompanyContext, IsCompanyAdmin, SameCompanyUser


class CompanyViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Acesso apenas à própria empresa (ou qualquer uma, se superusuário)."""

    serializer_class = CompanySerializer
    permission_classes = [HasCompanyContext]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Company.objects.all()
        return Company.objects.filter(pk=self.request.user.company_id)

    def get_object(self):
        if self.request.user.is_superuser:
            return get_object_or_404(Company, pk=self.kwargs["pk"])
        return get_object_or_404(Company, pk=self.request.user.company_id)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [HasCompanyContext, SameCompanyUser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all().order_by("email")
        return User.objects.filter(company_id=self.request.user.company_id).order_by("email")

    def get_permissions(self):
        if self.action in ("create", "destroy", "update", "partial_update"):
            return [HasCompanyContext(), IsCompanyAdmin()]
        return [HasCompanyContext()]
