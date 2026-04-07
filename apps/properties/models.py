from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import CompanyOwnedModel


class Property(CompanyOwnedModel):
    """Fazenda: cadastro enxuto (descrição livre + município)."""

    owner = models.ForeignKey(
        "masterdata.BusinessPartner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="properties",
        verbose_name="proprietário",
    )
    description = models.TextField("descrição")
    city = models.CharField("cidade", max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fazenda"
        verbose_name_plural = "Fazendas"

    def __str__(self):
        return f"{self.description} — {self.city}"


class Area(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="areas",
    )
    matricula = models.CharField("matrícula", max_length=120)
    description = models.TextField(blank=True)
    hectares = models.DecimalField(
        "hectares",
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )
    color = models.CharField(max_length=16, default="#3388ff")
    geometry = gis_models.MultiPolygonField(srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        constraints = [
            models.UniqueConstraint(
                fields=["property", "matricula"],
                name="properties_area_prop_matricula_uniq",
            ),
        ]

    def clean(self):
        super().clean()
        self.matricula = (self.matricula or "").strip()
        if not self.matricula:
            raise ValidationError({"matricula": "Informe a matrícula."})
        if self.property_id:
            qs = Area.objects.filter(property_id=self.property_id, matricula=self.matricula)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {
                        "matricula": "Já existe uma matrícula com este número nesta fazenda."
                    }
                )

    def save(self, *args, **kwargs):
        self.matricula = (self.matricula or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.matricula
