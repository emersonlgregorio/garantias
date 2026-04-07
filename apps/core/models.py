from django.db import models


class CompanyOwnedModel(models.Model):
    """Base para entidades com isolamento multiempresa direto."""

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True
