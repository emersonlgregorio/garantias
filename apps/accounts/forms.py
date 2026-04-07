import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import Company, User


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


class PublicSignupForm(forms.Form):
    """Cadastro público: empresa + primeiro usuário (admin da conta)."""

    company_name = forms.CharField(
        label="Razão social ou nome da empresa",
        max_length=255,
        widget=forms.TextInput(attrs={"autocomplete": "organization", "placeholder": "Ex.: Fazenda Santa Rita Ltda."}),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        max_length=18,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "00.000.000/0001-00"}),
    )
    email = forms.EmailField(
        label="E-mail corporativo",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "seu@email.com.br"}),
    )
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "Seu nome"}),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Sobrenome"}),
    )
    password1 = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirme a senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_cnpj(self):
        raw = self.cleaned_data.get("cnpj", "")
        digits = _digits_only(raw)
        if len(digits) != 14:
            raise ValidationError("Informe um CNPJ válido (14 dígitos).")
        if any(_digits_only(c) == digits for c in Company.objects.values_list("cnpj", flat=True)):
            raise ValidationError("Este CNPJ já está cadastrado.")
        return digits

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password1")
        p2 = data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("As senhas não conferem.")
        if p1:
            validate_password(p1)
        return data

    def save(self):
        """Cria Company + User administrador na mesma transação (chamar dentro de atomic)."""
        from django.db import transaction

        data = self.cleaned_data
        with transaction.atomic():
            company = Company.objects.create(
                name=data["company_name"].strip(),
                cnpj=data["cnpj"],
                plan=Company.Plan.FREE,
                status=Company.Status.ACTIVE,
            )
            user = User.objects.create_user(
                email=data["email"],
                password=data["password1"],
                company=company,
                role=User.Role.ADMIN,
                first_name=data.get("first_name", "") or "",
                last_name=data.get("last_name", "") or "",
                is_active=True,
            )
        return user
