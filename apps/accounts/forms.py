import re

from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import Company, User


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _luhn_ok(num: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", num or "")]
    if len(digits) < 12:
        return False
    s = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d * 2
            if d > 9:
                d -= 9
        s += d
    return s % 10 == 0


class SignupCompanyForm(forms.Form):
    """Etapa 1: dados da empresa para emissão de NF-e (sem e-mail NF-e nesta etapa)."""

    company_name = forms.CharField(
        label="Razão social",
        max_length=255,
        widget=forms.TextInput(attrs={"autocomplete": "organization", "placeholder": "Ex.: Fazenda Santa Rita Ltda."}),
    )
    trade_name = forms.CharField(
        label="Nome fantasia",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "organization", "placeholder": "Opcional"}),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        max_length=18,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "00.000.000/0001-00"}),
    )
    state_registration = forms.CharField(
        label="Inscrição estadual",
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Opcional"}),
    )
    municipal_registration = forms.CharField(
        label="Inscrição municipal",
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Opcional"}),
    )
    address_zip_code = forms.CharField(
        label="CEP",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "postal-code", "placeholder": "00000-000"}),
    )
    address_street = forms.CharField(
        label="Logradouro",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-line1"}),
    )
    address_number = forms.CharField(
        label="Número",
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-line2"}),
    )
    address_complement = forms.CharField(
        label="Complemento",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    address_neighborhood = forms.CharField(
        label="Bairro",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    address_city = forms.CharField(
        label="Cidade",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-level2"}),
    )
    address_state = forms.CharField(
        label="UF",
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-level1", "placeholder": "SP"}),
    )

    def clean_cnpj(self):
        raw = self.cleaned_data.get("cnpj", "")
        digits = _digits_only(raw)
        if len(digits) != 14:
            raise ValidationError("Informe um CNPJ válido (14 dígitos).")
        if Company.objects.filter(cnpj__in=[digits, raw]).exists() or any(
            _digits_only(c) == digits for c in Company.objects.values_list("cnpj", flat=True)
        ):
            raise ValidationError("Este CNPJ já está cadastrado.")
        return digits

    def clean_address_state(self):
        uf = (self.cleaned_data.get("address_state") or "").strip().upper()
        if uf and len(uf) != 2:
            raise ValidationError("UF deve ter 2 letras (ex.: SP).")
        return uf


class SignupPlansForm(forms.Form):
    """Etapa 2: seleção de módulos e 1 plano por módulo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.billing.models import Module, Plan

        self._modules = list(Module.objects.filter(is_active=True).order_by("name"))
        plans = (
            Plan.objects.select_related("module")
            .filter(is_active=True, module__is_active=True)
            .order_by("module__name", "price")
        )
        plans_by_module: dict[int, list[Plan]] = {}
        for p in plans:
            plans_by_module.setdefault(p.module_id, []).append(p)

        for m in self._modules:
            self.fields[f"module_{m.id}"] = forms.BooleanField(
                required=False,
                label=m.name,
            )
            self.fields[f"plan_{m.id}"] = forms.ChoiceField(
                required=False,
                label=f"Plano para {m.name}",
                choices=[("", "Selecione um plano")]
                + [(str(p.id), f"{p.name} — R$ {p.price}") for p in plans_by_module.get(m.id, [])],
            )

    @property
    def modules(self):
        return getattr(self, "_modules", [])

    def selected_plan_ids(self) -> list[int]:
        ids: list[int] = []
        for m in self.modules:
            if self.cleaned_data.get(f"module_{m.id}"):
                raw = self.cleaned_data.get(f"plan_{m.id}") or ""
                if not raw:
                    raise ValidationError(f"Selecione um plano para o módulo {m.name}.")
                try:
                    ids.append(int(raw))
                except ValueError:
                    raise ValidationError("Seleção inválida de plano.")
        if not ids:
            raise ValidationError("Selecione ao menos um módulo e um plano.")
        return ids


class SignupPasswordForm(forms.Form):
    """Etapa 3: usuário admin + senha com regras."""

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
        help_text="Mín. 8 caracteres, com letra maiúscula, minúscula e número.",
    )
    password2 = forms.CharField(
        label="Confirme a senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password1") or ""
        p2 = data.get("password2") or ""
        if p1 and p2 and p1 != p2:
            raise ValidationError("As senhas não conferem.")
        if len(p1) < 8:
            raise ValidationError("A senha deve ter no mínimo 8 caracteres.")
        if not re.search(r"[a-z]", p1):
            raise ValidationError("A senha deve conter ao menos uma letra minúscula.")
        if not re.search(r"[A-Z]", p1):
            raise ValidationError("A senha deve conter ao menos uma letra maiúscula.")
        if not re.search(r"\d", p1):
            raise ValidationError("A senha deve conter ao menos um número.")
        return data


class SignupPaymentForm(forms.Form):
    """Etapa 4: forma de pagamento (sem gateway, apenas coleta/validação)."""

    payment_method = forms.ChoiceField(
        label="Forma de pagamento",
        required=True,
        choices=[("", "Escolha…")] + list(Company.PaymentMethod.choices),
    )
    boleto_email = forms.EmailField(
        label="E-mail para receber o boleto",
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "financeiro@empresa.com.br"}),
    )

    card_confirmation_email = forms.EmailField(
        label="E-mail para receber a confirmação",
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "seu@email.com.br"}),
    )

    card_holder = forms.CharField(label="Nome no cartão", required=False, max_length=120)
    card_number = forms.CharField(label="Número do cartão", required=False, max_length=32)
    card_exp = forms.CharField(label="Validade (MM/AA)", required=False, max_length=5)
    card_cvv = forms.CharField(label="CVV", required=False, max_length=4)

    def clean(self):
        data = super().clean()
        pm = data.get("payment_method")
        if pm == Company.PaymentMethod.BOLETO:
            if not data.get("boleto_email"):
                raise ValidationError("Informe o e-mail para receber o boleto.")
        elif pm == Company.PaymentMethod.CARD:
            n = data.get("card_number") or ""
            exp = (data.get("card_exp") or "").strip()
            cvv = re.sub(r"\D", "", data.get("card_cvv") or "")
            if not data.get("card_holder"):
                raise ValidationError("Informe o nome no cartão.")
            if not _luhn_ok(n):
                raise ValidationError("Número de cartão inválido.")
            if not re.match(r"^\d{2}/\d{2}$", exp):
                raise ValidationError("Validade inválida. Use MM/AA.")
            if len(cvv) not in (3, 4):
                raise ValidationError("CVV inválido.")
            if not data.get("card_confirmation_email"):
                raise ValidationError("Informe o e-mail para receber a confirmação.")
        return data


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

    modules = forms.MultipleChoiceField(
        label="Módulos para iniciar",
        required=True,
        choices=[],
        widget=forms.CheckboxSelectMultiple(),
    )
    payment_method = forms.ChoiceField(
        label="Forma de pagamento",
        required=True,
        choices=Company.PaymentMethod.choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carrega módulos ativos (catálogo).
        from apps.billing.models import Module

        mods = Module.objects.filter(is_active=True).order_by("name").values_list("id", "name")
        self.fields["modules"].choices = [(str(i), n) for (i, n) in mods]

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
                preferred_payment_method=data["payment_method"],
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

            # Inicia trial (7 dias) para os módulos escolhidos (MVP: usa o plano mais caro do módulo).
            from datetime import timedelta
            from django.utils import timezone

            from apps.billing.models import Plan, Subscription
            from apps.billing.services.invoicing import ensure_pending_invoice_for_subscription

            today = timezone.localdate()
            trial_end = today + timedelta(days=7)
            module_ids = [int(x) for x in data.get("modules") or []]
            for mid in module_ids:
                plan = (
                    Plan.objects.filter(module_id=mid, is_active=True)
                    .order_by("-price")
                    .first()
                )
                if not plan:
                    continue
                sub, _ = Subscription.objects.get_or_create(
                    company_id=company.pk,
                    module_id=mid,
                    defaults={
                        "plan": plan,
                        "status": Subscription.Status.TRIAL,
                        "trial_end_date": trial_end,
                        "start_date": today,
                        "end_date": None,
                    },
                )
                sub.plan = plan
                sub.status = Subscription.Status.TRIAL
                sub.trial_end_date = trial_end
                sub.end_date = None
                sub.save(update_fields=["plan", "status", "trial_end_date", "end_date"])
                ensure_pending_invoice_for_subscription(sub)
        return user
