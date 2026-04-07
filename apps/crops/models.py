from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import CompanyOwnedModel
from apps.crops.services.commitments import validate_max_three_commitments


class CropSeason(CompanyOwnedModel):
    name = models.CharField(max_length=64)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "Safra"
        verbose_name_plural = "Safras"
        constraints = [
            models.UniqueConstraint(fields=("company", "name"), name="uniq_cropseason_company_name"),
        ]

    def __str__(self):
        return self.name


class Commitment(models.Model):
    guarantee = models.ForeignKey(
        "guarantees.Guarantee",
        on_delete=models.CASCADE,
        related_name="commitments",
    )
    crop_season = models.ForeignKey(
        CropSeason,
        on_delete=models.CASCADE,
        related_name="commitments",
    )
    value = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empenho"
        verbose_name_plural = "Empenhos"

    def clean(self):
        super().clean()
        if not self.guarantee_id or not self.crop_season_id:
            return
        if self.guarantee.company_id != self.crop_season.company_id:
            raise ValidationError("A safra e a garantia devem ser da mesma empresa.")

        validate_max_three_commitments(
            self.guarantee.property_id,
            self.crop_season_id,
            exclude_pk=self.pk,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
