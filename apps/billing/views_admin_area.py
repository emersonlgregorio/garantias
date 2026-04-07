from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form, ModelForm, CharField, EmailField, PasswordInput, ChoiceField
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.utils import timezone

from apps.accounts.models import Company, CompanyApiKey, User
from apps.billing.models import Invoice, Module, Plan, Subscription
from apps.billing.services.invoicing import ensure_pending_invoice_for_subscription


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if getattr(request.user, "role", None) != User.Role.ADMIN:
            messages.error(request, "Apenas administradores da empresa.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class CompanyForm(ModelForm):
    class Meta:
        model = Company
        fields = ["name", "cnpj", "status"]


class CreateAnalystUserForm(Form):
    email = EmailField()
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    password = CharField(widget=PasswordInput())


class AdminAreaHomeView(AdminRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "app/admin_area/index.html",
            {"active_nav": None},
        )


class AdminAreaCompanyView(AdminRequiredMixin, View):
    def get(self, request):
        form = CompanyForm(instance=request.user.company)
        return render(
            request,
            "app/admin_area/company.html",
            {"form": form, "active_nav": None},
        )

    def post(self, request):
        form = CompanyForm(request.POST, instance=request.user.company)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa atualizada.")
            return redirect("admin_area_company")
        return render(request, "app/admin_area/company.html", {"form": form, "active_nav": None})


class AdminAreaUsersView(AdminRequiredMixin, View):
    def get(self, request):
        users = User.objects.filter(company_id=request.user.company_id).order_by("email")
        form = CreateAnalystUserForm()
        return render(
            request,
            "app/admin_area/users.html",
            {"users": users, "form": form, "active_nav": None},
        )

    def post(self, request):
        users = User.objects.filter(company_id=request.user.company_id).order_by("email")
        form = CreateAnalystUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                User.objects.create_user(
                    email=data["email"],
                    password=data["password"],
                    company=request.user.company,
                    role=User.Role.ANALYST,
                    first_name=data.get("first_name") or "",
                    last_name=data.get("last_name") or "",
                    is_active=True,
                )
                messages.success(request, "Usuário analista criado.")
                return redirect("admin_area_users")
            except Exception:
                messages.error(request, "Não foi possível criar o usuário (e-mail já existe?).")
        return render(
            request,
            "app/admin_area/users.html",
            {"users": users, "form": form, "active_nav": None},
        )


class AdminAreaApiKeyView(AdminRequiredMixin, View):
    def get(self, request):
        api_key = CompanyApiKey.objects.filter(company_id=request.user.company_id).first()
        return render(
            request,
            "app/admin_area/api_key.html",
            {"api_key": api_key, "active_nav": None},
        )

    def post(self, request):
        api_key, created = CompanyApiKey.objects.get_or_create(
            company_id=request.user.company_id,
            defaults={"key": CompanyApiKey.generate_key()},
        )
        if not created:
            api_key.rotate()
        messages.success(request, "API key gerada/rotacionada.")
        return redirect("admin_area_api_key")


class AdminAreaInvoicesView(AdminRequiredMixin, View):
    def get(self, request):
        subs = list(
            Subscription.objects.select_related("plan", "module")
            .filter(company_id=request.user.company_id)
            .order_by("module__name")
        )
        sub = next((s for s in subs if s.module and s.module.key == "guarantees"), None)
        invoices = (
            Invoice.objects.select_related("subscription", "subscription__plan", "subscription__module")
            .filter(company_id=request.user.company_id)
            .order_by("-created_at")
        )
        return render(
            request,
            "app/admin_area/invoices.html",
            {
                "invoices": invoices,
                "current_subscription": sub,
                "subscriptions": subs,
                "active_nav": None,
            },
        )


class ChangePlanForm(Form):
    plan_id = ChoiceField(label="Novo plano", choices=[])

    def __init__(self, *, module: Module, **kwargs):
        super().__init__(**kwargs)
        qs = Plan.objects.filter(module=module, is_active=True).order_by("price")
        self.fields["plan_id"].choices = [(str(p.id), f"{p.name} — R$ {p.price}") for p in qs]


class AdminAreaChangePlanView(AdminRequiredMixin, View):
    module_key = "guarantees"

    def get_module(self) -> Module | None:
        return Module.objects.filter(key=self.module_key, is_active=True).first()

    def get(self, request):
        module = self.get_module()
        if not module:
            messages.error(request, "Módulo inválido.")
            return redirect("admin_area_invoices")
        sub = (
            Subscription.objects.select_related("plan", "module")
            .filter(company_id=request.user.company_id, module=module)
            .first()
        )
        form = ChangePlanForm(module=module)
        return render(
            request,
            "app/admin_area/change_plan.html",
            {"form": form, "module": module, "current_subscription": sub, "active_nav": None},
        )

    def post(self, request):
        module = self.get_module()
        if not module:
            messages.error(request, "Módulo inválido.")
            return redirect("admin_area_invoices")
        sub = (
            Subscription.objects.select_related("plan", "module")
            .filter(company_id=request.user.company_id, module=module)
            .first()
        )
        form = ChangePlanForm(module=module, data=request.POST)
        if not form.is_valid():
            return render(
                request,
                "app/admin_area/change_plan.html",
                {"form": form, "module": module, "current_subscription": sub, "active_nav": None},
            )

        if sub and sub.plan.billing_type == Plan.BillingType.YEARLY:
            today = timezone.localdate()
            if sub.end_date and sub.end_date >= today:
                messages.error(
                    request,
                    "Plano anual: alterações só são permitidas após o vencimento.",
                )
                return redirect("admin_area_invoices")

        plan = Plan.objects.filter(pk=int(form.cleaned_data["plan_id"]), module=module, is_active=True).first()
        if not plan:
            messages.error(request, "Plano inválido.")
            return redirect("admin_area_invoices")

        today = timezone.localdate()
        if not sub:
            sub = Subscription.objects.create(
                company_id=request.user.company_id,
                module=module,
                plan=plan,
                status=Subscription.Status.ACTIVE,
                start_date=today,
                end_date=None,
            )
        else:
            sub.plan = plan
            sub.status = Subscription.Status.ACTIVE
            sub.trial_end_date = None
            sub.start_date = today
            # Se anual, define vencimento em 1 ano para travar alterações até lá.
            if plan.billing_type == Plan.BillingType.YEARLY:
                sub.end_date = today.replace(year=today.year + 1)
            else:
                sub.end_date = None
            sub.save(update_fields=["plan", "status", "trial_end_date", "start_date", "end_date"])

        ensure_pending_invoice_for_subscription(sub)
        messages.success(request, "Plano atualizado.")
        return redirect("admin_area_invoices")
