from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import CompanyOwnedModel


class Guarantee(CompanyOwnedModel):
    class Type(models.TextChoices):
        CEDULA_RURAL = "CEDULA_RURAL", "Cédula rural"
        BARTER = "BARTER", "Barter"
        PENHOR = "PENHOR", "Penhor"
        OUTROS = "OUTROS", "Outros"

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="guarantees",
        verbose_name="fazenda",
    )
    crop_season = models.ForeignKey(
        "crops.CropSeason",
        on_delete=models.PROTECT,
        related_name="guarantees",
        verbose_name="safra",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    value = models.DecimalField(max_digits=18, decimal_places=2)
    issue_date = models.DateField()
    status = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    areas = models.ManyToManyField(
        "properties.Area",
        through="GuaranteeArea",
        related_name="guarantees",
    )

    class Meta:
        verbose_name = "Garantia"
        verbose_name_plural = "Garantias"

    def clean(self):
        super().clean()
        if self.property_id and self.company_id and self.property.company_id != self.company_id:
            raise ValidationError("A fazenda deve pertencer à mesma empresa da garantia.")
        if self.crop_season_id and self.company_id and self.crop_season.company_id != self.company_id:
            raise ValidationError("A safra deve pertencer à mesma empresa da garantia.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} — {self.property_id}"


class GuaranteeArea(models.Model):
    guarantee = models.ForeignKey(Guarantee, on_delete=models.CASCADE, related_name="guarantee_areas")
    area = models.ForeignKey("properties.Area", on_delete=models.CASCADE, related_name="guarantee_areas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("guarantee", "area"), name="uniq_guarantee_area"),
        ]

    def clean(self):
        super().clean()
        prop_company = self.area.property.company_id
        g_company = self.guarantee.company_id
        if prop_company != g_company:
            raise ValidationError("Área e garantia devem pertencer à mesma empresa (via fazenda).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
