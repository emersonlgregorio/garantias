from rest_framework import serializers

from apps.crops.models import Commitment, CropSeason
from apps.crops.services.commitments import validate_max_three_commitments
from apps.guarantees.models import Guarantee


class CropSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropSeason
        fields = ["id", "company", "name", "start_date", "end_date"]
        read_only_fields = ["company"]

    def create(self, validated_data):
        validated_data["company"] = self.context["request"].user.company
        return super().create(validated_data)


class CommitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commitment
        fields = ["id", "guarantee", "crop_season", "value", "created_at"]
        read_only_fields = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.context.get("request")
        if r and r.user.company_id:
            cid = r.user.company_id
            self.fields["guarantee"].queryset = Guarantee.objects.filter(company_id=cid)
            self.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)

    def validate(self, attrs):
        guarantee = attrs.get("guarantee")
        crop_season = attrs.get("crop_season")
        if guarantee is None:
            guarantee = getattr(self.instance, "guarantee", None)
        if crop_season is None:
            crop_season = getattr(self.instance, "crop_season", None)
        if guarantee and crop_season:
            if guarantee.company_id != crop_season.company_id:
                raise serializers.ValidationError("Garantia e safra devem ser da mesma empresa.")
            validate_max_three_commitments(
                guarantee.property_id,
                crop_season.pk,
                exclude_pk=self.instance.pk if self.instance else None,
            )
        return attrs
