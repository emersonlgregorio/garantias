from rest_framework import serializers

from apps.crops.models import CropSeason
from apps.guarantees.models import Guarantee
from apps.properties.models import Area, Property


class GuaranteeSerializer(serializers.ModelSerializer):
    areas = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
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
            "type",
            "value",
            "issue_date",
            "status",
            "created_at",
            "areas",
        ]
        read_only_fields = ["company", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.context.get("request")
        if r and r.user.company_id:
            cid = r.user.company_id
            self.fields["areas"].queryset = Area.objects.filter(property__company_id=cid)
            self.fields["property"].queryset = Property.objects.filter(company_id=cid)
            self.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)

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

    def create(self, validated_data):
        areas = validated_data.pop("areas", [])
        validated_data["company"] = self.context["request"].user.company
        g = Guarantee.objects.create(**validated_data)
        if areas:
            g.areas.set(areas)
        return g

    def update(self, instance, validated_data):
        areas = validated_data.pop("areas", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if areas is not None:
            instance.areas.set(areas)
        return instance
