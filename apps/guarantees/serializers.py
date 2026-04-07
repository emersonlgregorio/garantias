from rest_framework import serializers

from apps.crops.models import CropSeason
from apps.guarantees.models import Guarantee
from apps.masterdata.models import BusinessPartner, Currency, ProductionProduct
from apps.properties.models import Area, Property


class GuaranteeSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()

    areas = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        many=True,
        required=False,
    )
    products = serializers.PrimaryKeyRelatedField(
        queryset=ProductionProduct.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Guarantee
        fields = [
            "id",
            "company",
            "property",
            "crop_season",
            "principal_area",
            "business_partner",
            "currency",
            "type",
            "value",
            "issue_date",
            "due_date",
            "status",
            "status_display",
            "cpr",
            "pledge",
            "pledge_grade",
            "products",
            "created_at",
            "areas",
        ]
        read_only_fields = ["company", "created_at"]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.context.get("request")
        if r and r.user.company_id:
            cid = r.user.company_id
            self.fields["areas"].queryset = Area.objects.filter(property__company_id=cid)
            self.fields["property"].queryset = Property.objects.filter(company_id=cid)
            self.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            self.fields["principal_area"].queryset = Area.objects.filter(property__company_id=cid)
            self.fields["business_partner"].queryset = BusinessPartner.objects.filter(company_id=cid)
            self.fields["currency"].queryset = Currency.objects.filter(company_id=cid)
            self.fields["products"].queryset = ProductionProduct.objects.filter(company_id=cid)

    def validate_property(self, prop):
        if prop.company_id != self.context["request"].user.company_id:
            raise serializers.ValidationError("A fazenda não pertence à sua empresa.")
        return prop

    def validate_crop_season(self, season):
        if season is None:
            return season
        if season.company_id != self.context["request"].user.company_id:
            raise serializers.ValidationError("A safra não pertence à sua empresa.")
        return season

    def validate_areas(self, areas):
        cid = self.context["request"].user.company_id
        for a in areas:
            if a.property.company_id != cid:
                raise serializers.ValidationError("Todas as áreas devem ser da sua empresa.")
        return areas

    def validate_products(self, products):
        cid = self.context["request"].user.company_id
        for p in products:
            if p.company_id != cid:
                raise serializers.ValidationError("Todos os produtos devem ser da sua empresa.")
        return products

    def create(self, validated_data):
        areas = validated_data.pop("areas", [])
        products = validated_data.pop("products", [])
        validated_data["company"] = self.context["request"].user.company
        g = Guarantee.objects.create(**validated_data)
        if areas:
            g.areas.set(areas)
        if products:
            g.products.set(products)
        return g

    def update(self, instance, validated_data):
        areas = validated_data.pop("areas", None)
        products = validated_data.pop("products", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if areas is not None:
            instance.areas.set(areas)
        if products is not None:
            instance.products.set(products)
        return instance
