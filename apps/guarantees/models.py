from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import CompanyOwnedModel


class Guarantee(CompanyOwnedModel):
    class Type(models.TextChoices):
        CEDULA_RURAL = "CEDULA_RURAL", "Cédula rural"
        BARTER = "BARTER", "Barter"
        PENHOR = "PENHOR", "Penhor"
        OUTROS = "OUTROS", "Outros"

    class Status(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ATIVO = "ATIVO", "Ativo"
        BAIXADO = "BAIXADO", "Baixado"

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
    principal_area = models.ForeignKey(
        "properties.Area",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="principal_guarantees",
        verbose_name="matrícula principal",
    )
    business_partner = models.ForeignKey(
        "masterdata.BusinessPartner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="guarantees",
        verbose_name="parceiro de negócio",
    )
    currency = models.ForeignKey(
        "masterdata.Currency",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="guarantees",
        verbose_name="moeda",
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    value = models.DecimalField(max_digits=18, decimal_places=2)
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True, verbose_name="vencimento")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.SOLICITADO,
        verbose_name="status",
    )
    cpr = models.BooleanField(default=False, verbose_name="CPR")
    pledge = models.BooleanField(default=False, verbose_name="penhor")

    class PledgeGrade(models.TextChoices):
        NONE = "NONE", "Não"
        G1 = "G1", "1º"
        G2 = "G2", "2º"
        G3 = "G3", "3º"

    pledge_grade = models.CharField(
        max_length=8,
        choices=PledgeGrade.choices,
        default=PledgeGrade.NONE,
        verbose_name="grau do penhor",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    areas = models.ManyToManyField(
        "properties.Area",
        through="GuaranteeArea",
        related_name="guarantees",
    )
    products = models.ManyToManyField(
        "masterdata.ProductionProduct",
        related_name="guarantees",
        blank=True,
        verbose_name="produtos de produção",
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
        if self.principal_area_id and self.property_id and self.principal_area.property_id != self.property_id:
            raise ValidationError("A matrícula principal deve ser da mesma fazenda da garantia.")
        if self.business_partner_id and self.company_id and self.business_partner.company_id != self.company_id:
            raise ValidationError("O parceiro de negócio deve pertencer à mesma empresa da garantia.")
        if self.currency_id and self.company_id and self.currency.company_id != self.company_id:
            raise ValidationError("A moeda deve pertencer à mesma empresa da garantia.")

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
