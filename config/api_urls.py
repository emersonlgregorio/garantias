from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.viewsets import CompanyViewSet, UserViewSet
from apps.billing.viewsets import InvoiceViewSet, PlanViewSet, SubscriptionViewSet
from apps.billing.views_subscribe import SubscribeView
from apps.crops.viewsets import CommitmentViewSet, CropSeasonViewSet
from apps.guarantees.viewsets import GuaranteeViewSet
from apps.masterdata.viewsets import BusinessPartnerViewSet, CurrencyViewSet, ProductionProductViewSet
from apps.properties.viewsets import AreaViewSet, PropertyViewSet

router = DefaultRouter()
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"users", UserViewSet, basename="user")
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"areas", AreaViewSet, basename="area")
router.register(r"guarantees", GuaranteeViewSet, basename="guarantee")
router.register(r"crop-seasons", CropSeasonViewSet, basename="crop-season")
router.register(r"commitments", CommitmentViewSet, basename="commitment")
router.register(r"partners", BusinessPartnerViewSet, basename="partner")
router.register(r"production-products", ProductionProductViewSet, basename="production-product")
router.register(r"currencies", CurrencyViewSet, basename="currency")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("subscribe", SubscribeView.as_view(), name="subscribe"),
    path("", include(router.urls)),
]
