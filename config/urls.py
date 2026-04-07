from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path

from apps.accounts.views_public import LandingView, PublicSignupView
from apps.accounts.views_login import DashboardFirstLoginView
from apps.accounts.views_pricing import PricingView
from apps.accounts.views_subscribe_landing import SubscribeLandingView
from apps.core.views import DashboardView, MapPageView, oauth_prepare_stub
from apps.properties.views_map_print import MapAreasPdfView
from apps.billing.views_admin_area import (
    AdminAreaApiKeyView,
    AdminAreaChangePlanView,
    AdminAreaCompanyView,
    AdminAreaHomeView,
    AdminAreaInvoicesView,
    AdminAreaUsersView,
)
from apps.core.views_app import (
    BusinessPartnerCreateView,
    BusinessPartnerListView,
    BusinessPartnerUpdateView,
    CurrencyCreateView,
    CurrencyListView,
    CurrencyUpdateView,
    CropSeasonCreateView,
    CropSeasonListView,
    CropSeasonUpdateView,
    GuaranteeCreateView,
    GuaranteeListView,
    GuaranteeUpdateView,
    PropertyCreateView,
    PropertyListView,
    PropertyUpdateView,
    ProductionProductCreateView,
    ProductionProductListView,
    ProductionProductUpdateView,
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
    path("app/parceiros/", BusinessPartnerListView.as_view(), name="app_partners_list"),
    path("app/parceiros/novo/", BusinessPartnerCreateView.as_view(), name="app_partners_new"),
    path("app/parceiros/<int:pk>/editar/", BusinessPartnerUpdateView.as_view(), name="app_partners_edit"),

    path("app/safras/", CropSeasonListView.as_view(), name="app_crops_list"),
    path("app/safras/nova/", CropSeasonCreateView.as_view(), name="app_crops_new"),
    path("app/safras/<int:pk>/editar/", CropSeasonUpdateView.as_view(), name="app_crops_edit"),

    path("app/produtos-producao/", ProductionProductListView.as_view(), name="app_products_list"),
    path("app/produtos-producao/novo/", ProductionProductCreateView.as_view(), name="app_products_new"),
    path("app/produtos-producao/<int:pk>/editar/", ProductionProductUpdateView.as_view(), name="app_products_edit"),

    path("app/moedas/", CurrencyListView.as_view(), name="app_currencies_list"),
    path("app/moedas/nova/", CurrencyCreateView.as_view(), name="app_currencies_new"),
    path("app/moedas/<int:pk>/editar/", CurrencyUpdateView.as_view(), name="app_currencies_edit"),

    path("app/garantias/", GuaranteeListView.as_view(), name="app_guarantees_list"),
    path("app/garantias/nova/", GuaranteeCreateView.as_view(), name="app_guarantees_new"),
    path("app/garantias/<int:pk>/editar/", GuaranteeUpdateView.as_view(), name="app_guarantees_edit"),
    path("admin-area/", AdminAreaHomeView.as_view(), name="admin_area"),
    path("admin-area/empresa/", AdminAreaCompanyView.as_view(), name="admin_area_company"),
    path("admin-area/usuarios/", AdminAreaUsersView.as_view(), name="admin_area_users"),
    path("admin-area/api-key/", AdminAreaApiKeyView.as_view(), name="admin_area_api_key"),
    path("admin-area/faturas/", AdminAreaInvoicesView.as_view(), name="admin_area_invoices"),
    path("admin-area/plano/", AdminAreaChangePlanView.as_view(), name="admin_area_change_plan"),
    path("accounts/login/", DashboardFirstLoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", PublicSignupView.as_view(), name="signup"),
    path("landing/precos/", PricingView.as_view(), name="landing_pricing"),
    path("landing/assinar/", SubscribeLandingView.as_view(), name="subscribe_landing"),
    path("oauth/", oauth_prepare_stub),
    path("health/", lambda r: JsonResponse({"status": "ok"})),
    path("", LandingView.as_view(), name="landing"),
]
