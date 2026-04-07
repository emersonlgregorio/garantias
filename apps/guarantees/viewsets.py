from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.decorators import action
from weasyprint import HTML

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
