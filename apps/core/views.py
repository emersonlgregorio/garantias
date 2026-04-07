import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView


def oauth_prepare_stub(_request):
    """Reserva rota para OAuth (Google / Microsoft Entra). Implementar fluxo real com credenciais."""
    return JsonResponse(
        {
            "detail": "OAuth não configurado. Preparar django-allauth ou social-auth-app-django + apps registrados.",
            "prepared_providers": ["google", "microsoft_entra"],
        },
        status=501,
    )


class MapPageView(LoginRequiredMixin, TemplateView):
    """Página do mapa (Leaflet + desenho). Requer sessão autenticada."""

    template_name = "map/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["map_provider"] = getattr(settings, "MAP_PROVIDER", "leaflet")
        ctx["map_tile_url"] = getattr(settings, "MAP_TILE_URL", "")
        ctx["map_tile_attribution"] = getattr(settings, "MAP_TILE_ATTRIBUTION", "")
        ctx["map_tile_max_zoom"] = getattr(settings, "MAP_TILE_MAX_ZOOM", 19)
        ctx["map_labels_tile_url"] = getattr(settings, "MAP_LABELS_TILE_URL", "")
        ctx["map_labels_attribution"] = getattr(settings, "MAP_LABELS_ATTRIBUTION", "")
        ctx["map_labels_opacity"] = getattr(settings, "MAP_LABELS_OPACITY", 1.0)
        ctx["map_road_tile_url"] = getattr(settings, "MAP_ROAD_TILE_URL", "")
        ctx["map_road_tile_attribution"] = getattr(settings, "MAP_ROAD_TILE_ATTRIBUTION", "")
        ctx["jwt_obtain_url"] = "/api/v1/auth/token/"
        ctx["api_root"] = "/api/v1/"
        user = self.request.user
        ctx["api_user_context"] = json.dumps(
            {
                "email": user.email,
                "company_id": user.company_id,
                "is_staff": user.is_staff,
            }
        )
        ctx["active_nav"] = "map"
        ctx["map_print_pdf_url"] = reverse("map_areas_pdf")
        return ctx


from django.contrib.gis.db.models.functions import Area as GeoArea, Transform
from django.db.models import FloatField, Sum

from apps.guarantees.models import Guarantee
from apps.properties.models import Area as LandArea, Property


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "app/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser or not user.company_id:
            props_qs = Property.objects.none()
            areas_qs = LandArea.objects.none()
            g_qs = Guarantee.objects.none()
        else:
            props_qs = Property.objects.filter(company_id=user.company_id)
            areas_qs = LandArea.objects.filter(property__company_id=user.company_id)
            g_qs = Guarantee.objects.filter(company_id=user.company_id)

        ctx["properties_count"] = props_qs.count()
        ctx["areas_count"] = areas_qs.count()
        ctx["guarantees_count"] = g_qs.count()

        agg = areas_qs.aggregate(
            m2=Sum(GeoArea(Transform("geometry", 3857)), output_field=FloatField())
        )
        total_m2 = agg.get("m2")
        ctx["total_ha"] = (float(total_m2) / 10000.0) if total_m2 is not None else 0.0
        ctx["active_nav"] = "dashboard"
        return ctx
