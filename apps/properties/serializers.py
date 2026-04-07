from django.contrib.gis.geos import MultiPolygon
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.properties.models import Area, Property


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            "id",
            "company",
            "description",
            "city",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.context.get("request")
        if r and r.user.is_authenticated and not r.user.is_superuser:
            self.fields["company"].read_only = True

    def create(self, validated_data):
        r = self.context["request"]
        if r.user.is_superuser and not validated_data.get("company"):
            raise serializers.ValidationError({"company": "Obrigatório para superusuário."})
        if not r.user.is_superuser:
            validated_data["company"] = r.user.company
        return super().create(validated_data)


class AreaSerializer(GeoFeatureModelSerializer):
    """GeoJSON Feature via campo `geometry` (MultiPolygon, SRID 4326)."""

    linked_guarantee_count = serializers.SerializerMethodField()

    class Meta:
        model = Area
        geo_field = "geometry"
        fields = [
            "id",
            "property",
            "matricula",
            "description",
            "hectares",
            "color",
            "created_at",
            "linked_guarantee_count",
        ]
        read_only_fields = ["created_at", "linked_guarantee_count"]

    def get_linked_guarantee_count(self, obj):
        c = getattr(obj, "linked_guarantee_count", None)
        if c is not None:
            return c
        return obj.guarantees.count()

    def validate(self, attrs):
        g = attrs.get("geometry")
        if g is not None and g.geom_type == "Polygon":
            attrs["geometry"] = MultiPolygon(g)
        if self.instance is None and attrs.get("hectares") is None:
            raise serializers.ValidationError(
                {"hectares": "Informe os hectares."}
            )
        return attrs

    def validate_matricula(self, value):
        s = (value or "").strip()
        if not s:
            raise serializers.ValidationError("Informe a matrícula.")
        return s

    def validate_property(self, prop):
        if prop.company_id != self.context["request"].user.company_id:
            raise serializers.ValidationError("A fazenda não pertence à sua empresa.")
        return prop
