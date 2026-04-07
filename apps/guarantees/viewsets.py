from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from weasyprint import HTML

from apps.billing.services.entitlements import can_print, ensure_module_access
from apps.core.mixins import CompanyScopedQuerysetMixin
from apps.core.permissions import BelongsToUserCompany, HasCompanyContext
from apps.guarantees.models import Guarantee
from apps.guarantees.serializers import GuaranteeSerializer


class GuaranteeViewSet(CompanyScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = GuaranteeSerializer
    permission_classes = [HasCompanyContext, BelongsToUserCompany]
    queryset = Guarantee.objects.select_related(
        "company", "property", "crop_season"
    ).prefetch_related("areas").all()

    def get_queryset(self):
        qs = self.scope_queryset(super().get_queryset())
        pid = self.request.query_params.get("property")
        if pid:
            qs = qs.filter(property_id=pid)
        cs = self.request.query_params.get("crop_season")
        if cs:
            qs = qs.filter(crop_season_id=cs)
        return qs

    def _ensure_can_edit_when_locked(self) -> None:
        user = self.request.user
        if not user or not user.is_authenticated or user.is_superuser:
            return
        cid = getattr(user, "company_id", None)
        if cid is None:
            raise PermissionDenied("Usuário sem empresa vinculada.")
        sub = ensure_module_access(company_id=cid, module_key="guarantees")
        if sub.is_locked:
            raise PermissionDenied(
                "Plano travado após a primeira impressão; não é permitido alterar/excluir garantias."
            )

    def update(self, request, *args, **kwargs):
        self._ensure_can_edit_when_locked()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_can_edit_when_locked()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_can_edit_when_locked()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="export")
    def export_html(self, request, pk=None):
        guarantee = self.get_object()
        body = render_to_string(
            "export/guarantee.html",
            {"guarantee": guarantee},
            request=request,
        )
        return HttpResponse(body)

    @action(detail=True, methods=["get"], url_path="export.pdf")
    def export_pdf(self, request, pk=None):
        if not request.user.is_superuser:
            cid = getattr(request.user, "company_id", None)
            if cid is None:
                raise PermissionDenied("Usuário sem empresa vinculada.")
            sub = ensure_module_access(company_id=cid, module_key="guarantees")
            if not can_print(sub):
                raise PermissionDenied("Seu plano atual não permite imprimir PDF.")
        guarantee = self.get_object()
        body = render_to_string(
            "export/guarantee.html",
            {"guarantee": guarantee},
            request=request,
        )
        pdf_bytes = HTML(string=body, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="garantia-{guarantee.pk}.pdf"'
        return response
