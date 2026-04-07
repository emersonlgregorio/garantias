from django.contrib import admin

from apps.masterdata.models import BusinessPartner, Currency, ProductionProduct


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "company", "created_at")
    search_fields = ("name", "cnpj")


@admin.register(ProductionProduct)
class ProductionProductAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "company", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

