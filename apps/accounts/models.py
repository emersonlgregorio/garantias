from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import secrets


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class Company(models.Model):
    class Plan(models.TextChoices):
        FREE = "FREE", "Gratuito"
        PRO = "PRO", "Profissional"
        ENTERPRISE = "ENTERPRISE", "Enterprise"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        SUSPENDED = "SUSPENDED", "Suspensa"

    class PaymentMethod(models.TextChoices):
        BOLETO = "BOLETO", "Boleto"
        CARD = "CARD", "Cartão de crédito"

    name = models.CharField("razão social / nome", max_length=255)
    trade_name = models.CharField("nome fantasia", max_length=255, blank=True, default="")
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    state_registration = models.CharField("inscrição estadual", max_length=32, blank=True, default="")
    municipal_registration = models.CharField("inscrição municipal", max_length=32, blank=True, default="")

    address_zip_code = models.CharField("CEP", max_length=12, blank=True, default="")
    address_street = models.CharField("logradouro", max_length=255, blank=True, default="")
    address_number = models.CharField("número", max_length=32, blank=True, default="")
    address_complement = models.CharField("complemento", max_length=255, blank=True, default="")
    address_neighborhood = models.CharField("bairro", max_length=120, blank=True, default="")
    address_city = models.CharField("cidade", max_length=120, blank=True, default="")
    address_state = models.CharField("UF", max_length=2, blank=True, default="")

    nfe_email = models.EmailField("e-mail para NF-e", blank=True, default="")
    plan = models.CharField(max_length=32, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    preferred_payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        blank=True,
        default="",
    )
    boleto_email = models.EmailField("e-mail para boleto", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name


class CompanyApiKey(models.Model):
    """Chave de API por empresa (MVP: armazena em texto)."""

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="api_key",
    )
    key = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API Key da empresa"
        verbose_name_plural = "API Keys das empresas"

    @staticmethod
    def generate_key() -> str:
        return "tgk_" + secrets.token_urlsafe(32)

    def rotate(self) -> str:
        self.key = self.generate_key()
        self.rotated_at = timezone.now()
        self.save(update_fields=["key", "rotated_at"])
        return self.key

    def __str__(self) -> str:
        return f"{self.company} (API key)"


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ANALYST = "analyst", "Analista"
        USER = "user", "Usuário"

    username = None
    email = models.EmailField("e-mail", unique=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.USER)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.email
