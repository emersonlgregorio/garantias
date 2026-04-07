"""Regras de negócio para empenhos (commitments)."""

from django.core.exceptions import ValidationError


def count_commitments_for_property_and_season(property_id: int, crop_season_id: int, exclude_pk: int | None = None) -> int:
    from apps.crops.models import Commitment

    qs = Commitment.objects.filter(
        guarantee__property_id=property_id,
        crop_season_id=crop_season_id,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.count()


def validate_max_three_commitments(property_id: int, crop_season_id: int, exclude_pk: int | None = None) -> None:
    if count_commitments_for_property_and_season(property_id, crop_season_id, exclude_pk) >= 3:
        raise ValidationError("Máximo de 3 empenhos permitidos por imóvel e safra.")
