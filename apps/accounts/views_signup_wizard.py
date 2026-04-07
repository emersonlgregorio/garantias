from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from apps.accounts.forms import (
    SignupCompanyForm,
    SignupPasswordForm,
    SignupPaymentForm,
    SignupPlansForm,
)
from apps.accounts.models import Company, User
from apps.billing.models import Plan, Subscription
from apps.billing.services.invoicing import ensure_pending_invoice_for_subscription


WIZ_KEY = "signup_wizard_v1"


def _get_step(request) -> int:
    try:
        s = int(request.GET.get("step") or request.POST.get("step") or 1)
    except ValueError:
        s = 1
    return 1 if s < 1 else 4 if s > 4 else s


def _get_state(request) -> dict:
    return dict(request.session.get(WIZ_KEY) or {})


def _set_state(request, state: dict) -> None:
    request.session[WIZ_KEY] = state
    request.session.modified = True


def _clear_state(request) -> None:
    if WIZ_KEY in request.session:
        del request.session[WIZ_KEY]
        request.session.modified = True


class SignupWizardView(View):
    template_name = "accounts/signup.html"

    def get(self, request):
        step = _get_step(request)
        state = _get_state(request)

        if step == 1:
            form = SignupCompanyForm(initial=state.get("company") or {})
        elif step == 2:
            form = SignupPlansForm(initial=state.get("plans") or {})
        elif step == 3:
            form = SignupPasswordForm(initial=state.get("user") or {})
        else:
            form = SignupPaymentForm(initial=state.get("payment") or {})

        return render(
            request,
            self.template_name,
            {"form": form, "step": step, "total_steps": 4},
        )

    def post(self, request):
        step = _get_step(request)
        state = _get_state(request)

        if step == 1:
            form = SignupCompanyForm(request.POST)
            if not form.is_valid():
                return render(request, self.template_name, {"form": form, "step": step, "total_steps": 4})
            state["company"] = form.cleaned_data
            _set_state(request, state)
            return redirect(reverse("signup") + "?step=2")

        if step == 2:
            form = SignupPlansForm(request.POST)
            if not form.is_valid():
                return render(request, self.template_name, {"form": form, "step": step, "total_steps": 4})
            try:
                plan_ids = form.selected_plan_ids()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, {"form": form, "step": step, "total_steps": 4})
            state["plans"] = {"plan_ids": [str(x) for x in plan_ids]}
            _set_state(request, state)
            return redirect(reverse("signup") + "?step=3")

        if step == 3:
            form = SignupPasswordForm(request.POST)
            if not form.is_valid():
                return render(request, self.template_name, {"form": form, "step": step, "total_steps": 4})
            state["user"] = {
                "email": form.cleaned_data["email"],
                "first_name": form.cleaned_data.get("first_name") or "",
                "last_name": form.cleaned_data.get("last_name") or "",
                # NÃO armazenar a senha em sessão
            }
            state["user_password"] = form.cleaned_data["password1"]
            _set_state(request, state)
            return redirect(reverse("signup") + "?step=4")

        # step 4: finalizar
        form = SignupPaymentForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "step": step, "total_steps": 4})

        company_data = state.get("company") or {}
        plans_data = state.get("plans") or {}
        user_data = state.get("user") or {}
        pwd = state.get("user_password") or ""
        plan_ids = [int(x) for x in (plans_data.get("plan_ids") or [])]
        if not company_data or not user_data or not pwd or not plan_ids:
            messages.error(request, "Cadastro incompleto. Refaça o fluxo.")
            _clear_state(request)
            return redirect(reverse("signup"))

        payment_data = form.cleaned_data
        today = timezone.localdate()
        trial_end = today + timedelta(days=7)

        with transaction.atomic():
            company = Company.objects.create(
                name=company_data.get("company_name", "").strip(),
                trade_name=(company_data.get("trade_name") or "").strip(),
                cnpj=company_data.get("cnpj"),
                state_registration=(company_data.get("state_registration") or "").strip(),
                municipal_registration=(company_data.get("municipal_registration") or "").strip(),
                address_zip_code=(company_data.get("address_zip_code") or "").strip(),
                address_street=(company_data.get("address_street") or "").strip(),
                address_number=(company_data.get("address_number") or "").strip(),
                address_complement=(company_data.get("address_complement") or "").strip(),
                address_neighborhood=(company_data.get("address_neighborhood") or "").strip(),
                address_city=(company_data.get("address_city") or "").strip(),
                address_state=(company_data.get("address_state") or "").strip(),
                plan=Company.Plan.FREE,
                status=Company.Status.ACTIVE,
                preferred_payment_method=payment_data["payment_method"],
                boleto_email=(payment_data.get("boleto_email") or "").strip(),
            )

            user = User.objects.create_user(
                email=user_data.get("email"),
                password=pwd,
                company=company,
                role=User.Role.ADMIN,
                first_name=user_data.get("first_name", "") or "",
                last_name=user_data.get("last_name", "") or "",
                is_active=True,
            )

            plans = list(
                Plan.objects.select_related("module")
                .filter(pk__in=plan_ids, is_active=True, module__is_active=True)
            )
            # 1 subscription por módulo
            by_module: dict[int, Plan] = {}
            for p in plans:
                by_module[p.module_id] = p
            for mid, plan in by_module.items():
                sub = Subscription.objects.create(
                    company_id=company.pk,
                    module_id=mid,
                    plan=plan,
                    status=Subscription.Status.TRIAL,
                    trial_end_date=trial_end,
                    start_date=today,
                    end_date=None,
                )
                ensure_pending_invoice_for_subscription(sub)

        _clear_state(request)
        messages.success(request, "Conta criada com sucesso. Faça login com seu e-mail e senha para continuar.")
        return redirect("login")

