from django.db import models
from django.utils import timezone


class Module(models.Model):
    """Catálogo de módulos do produto (ex.: Garantias, Planejamento)."""

    key = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"

    def __str__(self) -> str:
        return self.name


class Plan(models.Model):
    class BillingType(models.TextChoices):
        MONTHLY = "MONTHLY", "Mensal"
        YEARLY = "YEARLY", "Anual"
        PER_UNIT = "PER_UNIT", "Por unidade"

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="plans"
    )
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    billing_type = models.CharField(
        max_length=16, choices=BillingType.choices, default=BillingType.MONTHLY
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plano (catálogo)"
        verbose_name_plural = "Planos (catálogo)"
        constraints = [
            models.UniqueConstraint(fields=("module", "name"), name="uniq_plan_module_name"),
        ]

    def __str__(self):
        return f"{self.module.name} — {self.name}"


class PlanFeature(models.Model):
    """Configuração de capacidades/limites por plano (evita regras hardcoded)."""

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="features")
    key = models.CharField(max_length=160)
    value = models.JSONField()

    class Meta:
        verbose_name = "Feature do plano"
        verbose_name_plural = "Features do plano"
        constraints = [
            models.UniqueConstraint(fields=("plan", "key"), name="uniq_planfeature_plan_key"),
        ]

    def __str__(self) -> str:
        return f"{self.plan} · {self.key}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Ativa"
        EXPIRED = "EXPIRED", "Expirada"
        CANCELED = "CANCELED", "Cancelada"

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.TRIAL)
    trial_end_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    lock_reason = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        constraints = [
            models.UniqueConstraint(
                fields=("company", "module"), name="uniq_subscription_company_module"
            ),
        ]

    def __str__(self):
        return f"{self.company} → {self.plan}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PAID = "PAID", "Paga"
        CANCELED = "CANCELED", "Cancelada"

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company} · {self.amount} · {self.get_status_display()}"
