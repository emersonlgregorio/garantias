from rest_framework import serializers

from apps.masterdata.models import BusinessPartner, Currency, ProductionProduct


class BusinessPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPartner
        fields = ["id", "company", "name", "cnpj", "created_at"]
        read_only_fields = ["company", "created_at"]


class ProductionProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionProduct
        fields = ["id", "company", "name", "is_active", "created_at"]
        read_only_fields = ["company", "created_at"]


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "company", "code", "name", "symbol", "is_active"]
        read_only_fields = ["company"]

