from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import CompanyOwnedModel


def _digits_only(v: str) -> str:
    return re.sub(r"\D", "", v or "")


class BusinessPartner(CompanyOwnedModel):
    name = models.CharField("nome", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Parceiro de negócio"
        verbose_name_plural = "Parceiros de negócio"
        constraints = [
            models.UniqueConstraint(fields=("company", "cnpj"), name="uniq_partner_company_cnpj"),
        ]

    def clean(self):
        super().clean()
        if self.cnpj:
            self.cnpj = _digits_only(self.cnpj)
            if len(self.cnpj) != 14:
                raise ValidationError("Informe um CNPJ válido (14 dígitos) ou deixe em branco.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ProductionProduct(CompanyOwnedModel):
    name = models.CharField("nome", max_length=160)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produto de produção"
        verbose_name_plural = "Produtos de produção"
        constraints = [
            models.UniqueConstraint(fields=("company", "name"), name="uniq_prodproduct_company_name"),
        ]

    def __str__(self) -> str:
        return self.name


class Currency(CompanyOwnedModel):
    code = models.CharField("código", max_length=8)
    name = models.CharField("nome", max_length=64)
    symbol = models.CharField("símbolo", max_length=8, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Moeda"
        verbose_name_plural = "Moedas"
        constraints = [
            models.UniqueConstraint(fields=("company", "code"), name="uniq_currency_company_code"),
        ]

    def clean(self):
        super().clean()
        self.code = (self.code or "").strip().upper()
        if not self.code:
            raise ValidationError("Código da moeda é obrigatório.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

