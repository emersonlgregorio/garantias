from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path

from apps.accounts.views_public import LandingView, PublicSignupView
from apps.core.views import DashboardView, MapPageView, oauth_prepare_stub
from apps.properties.views_map_print import MapAreasPdfView
from apps.core.views_app import (
    CropSeasonCreateView,
    CropSeasonListView,
    CropSeasonUpdateView,
    GuaranteeCreateView,
    GuaranteeListView,
    GuaranteeUpdateView,
    PropertyCreateView,
    PropertyListView,
    PropertyUpdateView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api_urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("map/", MapPageView.as_view(), name="map"),
    path("map/imprimir.pdf", MapAreasPdfView.as_view(), name="map_areas_pdf"),
    path("app/propriedades/", PropertyListView.as_view(), name="app_properties_list"),
    path("app/propriedades/nova/", PropertyCreateView.as_view(), name="app_properties_new"),
    path("app/propriedades/<int:pk>/editar/", PropertyUpdateView.as_view(), name="app_properties_edit"),

    path("app/safras/", CropSeasonListView.as_view(), name="app_crops_list"),
    path("app/safras/nova/", CropSeasonCreateView.as_view(), name="app_crops_new"),
    path("app/safras/<int:pk>/editar/", CropSeasonUpdateView.as_view(), name="app_crops_edit"),

    path("app/garantias/", GuaranteeListView.as_view(), name="app_guarantees_list"),
    path("app/garantias/nova/", GuaranteeCreateView.as_view(), name="app_guarantees_new"),
    path("app/garantias/<int:pk>/editar/", GuaranteeUpdateView.as_view(), name="app_guarantees_edit"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", PublicSignupView.as_view(), name="signup"),
    path("oauth/", oauth_prepare_stub),
    path("health/", lambda r: JsonResponse({"status": "ok"})),
    path("", LandingView.as_view(), name="landing"),
]
