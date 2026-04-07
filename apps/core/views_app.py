from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from django.forms import DateInput, TextInput
from django.forms import ModelChoiceField, ModelForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from apps.crops.models import CropSeason
from apps.guarantees.models import Guarantee
from apps.billing.services.entitlements import ensure_module_access, get_limit
from apps.masterdata.models import BusinessPartner
from apps.masterdata.models import Currency, ProductionProduct
from apps.properties.models import Area, Property


class CompanyScopedMixin(LoginRequiredMixin):
    active_nav = "dashboard"

    def company_id(self):
        if self.request.user.is_superuser:
            return None
        return self.request.user.company_id

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_nav"] = self.active_nav
        return ctx


# -------------------- Propriedades --------------------


class PropertyForm(ModelForm):
    class Meta:
        model = Property
        fields = ["description", "city", "owner"]
        widgets = {
            "description": TextInput(),
        }


class PropertyListView(CompanyScopedMixin, ListView):
    template_name = "app/properties/list.html"
    context_object_name = "properties"
    active_nav = "properties"

    def get_queryset(self):
        cid = self.company_id()
        qs = Property.objects.select_related("company").order_by("-created_at")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["can_create"] = True
        if not user.is_superuser and user.company_id:
            try:
                sub = ensure_module_access(company_id=user.company_id, module_key="guarantees")
                lim = get_limit(sub, "limits.max_properties")
                if lim is not None and self.get_queryset().count() >= lim:
                    ctx["can_create"] = False
            except PermissionError:
                ctx["can_create"] = False
        return ctx


class PropertyCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/properties/form.html"
    active_nav = "properties"

    def get(self, request, *args, **kwargs):
        form = PropertyForm()
        cid = self.company_id()
        if cid is not None:
            form.fields["owner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "create"})

    def post(self, request, *args, **kwargs):
        form = PropertyForm(request.POST)
        cid = self.company_id()
        if cid is not None:
            form.fields["owner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            messages.success(request, "Fazenda criada com sucesso.")
            return redirect("app_properties_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "create"})


class PropertyUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/properties/form.html"
    active_nav = "properties"

    def get_object(self):
        cid = self.company_id()
        qs = Property.objects.all()
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = PropertyForm(instance=obj)
        cid = self.company_id()
        if cid is not None:
            form.fields["owner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = PropertyForm(request.POST, instance=obj)
        cid = self.company_id()
        if cid is not None:
            form.fields["owner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
        if form.is_valid():
            form.save()
            messages.success(request, "Fazenda atualizada.")
            return redirect("app_properties_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})


# -------------------- Dados Mestres (Parceiros / Produtos / Moedas) --------------------


class BusinessPartnerForm(ModelForm):
    class Meta:
        model = BusinessPartner
        fields = ["name", "cnpj"]


class BusinessPartnerListView(CompanyScopedMixin, ListView):
    template_name = "app/masterdata/partners_list.html"
    context_object_name = "partners"
    active_nav = "partners"

    def get_queryset(self):
        cid = self.company_id()
        qs = BusinessPartner.objects.select_related("company").order_by("name")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs


class BusinessPartnerCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/partners_form.html"
    active_nav = "partners"

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {"form": BusinessPartnerForm(), "active_nav": self.active_nav, "mode": "create"}
        )

    def post(self, request, *args, **kwargs):
        form = BusinessPartnerForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            messages.success(request, "Parceiro criado com sucesso.")
            return redirect("app_partners_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "create"}
        )


class BusinessPartnerUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/partners_form.html"
    active_nav = "partners"

    def get_object(self):
        cid = self.company_id()
        qs = BusinessPartner.objects.all()
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = BusinessPartnerForm(instance=obj)
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = BusinessPartnerForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Parceiro atualizado.")
            return redirect("app_partners_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )


class ProductionProductForm(ModelForm):
    class Meta:
        model = ProductionProduct
        fields = ["name", "is_active"]


class ProductionProductListView(CompanyScopedMixin, ListView):
    template_name = "app/masterdata/products_list.html"
    context_object_name = "products"
    active_nav = "products"

    def get_queryset(self):
        cid = self.company_id()
        qs = ProductionProduct.objects.select_related("company").order_by("name")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs


class ProductionProductCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/products_form.html"
    active_nav = "products"

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {"form": ProductionProductForm(), "active_nav": self.active_nav, "mode": "create"}
        )

    def post(self, request, *args, **kwargs):
        form = ProductionProductForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            messages.success(request, "Produto criado com sucesso.")
            return redirect("app_products_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "create"}
        )


class ProductionProductUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/products_form.html"
    active_nav = "products"

    def get_object(self):
        cid = self.company_id()
        qs = ProductionProduct.objects.all()
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = ProductionProductForm(instance=obj)
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = ProductionProductForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado.")
            return redirect("app_products_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )


class CurrencyForm(ModelForm):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol", "is_active"]


class CurrencyListView(CompanyScopedMixin, ListView):
    template_name = "app/masterdata/currencies_list.html"
    context_object_name = "currencies"
    active_nav = "currencies"

    def get_queryset(self):
        cid = self.company_id()
        qs = Currency.objects.select_related("company").order_by("code")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs


class CurrencyCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/currencies_form.html"
    active_nav = "currencies"

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {"form": CurrencyForm(), "active_nav": self.active_nav, "mode": "create"}
        )

    def post(self, request, *args, **kwargs):
        form = CurrencyForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            messages.success(request, "Moeda criada com sucesso.")
            return redirect("app_currencies_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "create"}
        )


class CurrencyUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/masterdata/currencies_form.html"
    active_nav = "currencies"

    def get_object(self):
        cid = self.company_id()
        qs = Currency.objects.all()
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = CurrencyForm(instance=obj)
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = CurrencyForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Moeda atualizada.")
            return redirect("app_currencies_list")
        return self.render_to_response(
            {"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj}
        )


# -------------------- Safras --------------------


class CropSeasonForm(ModelForm):
    class Meta:
        model = CropSeason
        fields = ["name", "start_date", "end_date"]


class CropSeasonListView(CompanyScopedMixin, ListView):
    template_name = "app/crops/list.html"
    context_object_name = "seasons"
    active_nav = "crops"

    def get_queryset(self):
        cid = self.company_id()
        qs = CropSeason.objects.select_related("company").order_by("-start_date")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["can_create"] = True
        if not user.is_superuser and user.company_id:
            try:
                sub = ensure_module_access(company_id=user.company_id, module_key="guarantees")
                lim = get_limit(sub, "limits.max_crop_seasons")
                if lim is not None and self.get_queryset().count() >= lim:
                    ctx["can_create"] = False
            except PermissionError:
                ctx["can_create"] = False
        return ctx


class CropSeasonCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/crops/form.html"
    active_nav = "crops"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": CropSeasonForm(), "active_nav": self.active_nav, "mode": "create"})

    def post(self, request, *args, **kwargs):
        form = CropSeasonForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            messages.success(request, "Safra criada com sucesso.")
            return redirect("app_crops_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "create"})


class CropSeasonUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/crops/form.html"
    active_nav = "crops"

    def get_object(self):
        cid = self.company_id()
        qs = CropSeason.objects.all()
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = CropSeasonForm(instance=obj)
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = CropSeasonForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Safra atualizada.")
            return redirect("app_crops_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})


# -------------------- Garantias --------------------


class GuaranteeForm(ModelForm):
    product = ModelChoiceField(
        queryset=ProductionProduct.objects.none(),
        required=False,
        label="Produto",
    )

    class Meta:
        model = Guarantee
        fields = [
            "property",
            "crop_season",
            "principal_area",
            "business_partner",
            "currency",
            "type",
            "value",
            "issue_date",
            "due_date",
            "status",
            "cpr",
            "pledge",
            "pledge_grade",
            "product",
        ]
        widgets = {
            "due_date": DateInput(attrs={"type": "date"}),
            "issue_date": DateInput(attrs={"type": "date"}),
        }


class GuaranteeListView(CompanyScopedMixin, ListView):
    template_name = "app/guarantees/list.html"
    context_object_name = "guarantees"
    active_nav = "guarantees"

    def get_queryset(self):
        cid = self.company_id()
        qs = Guarantee.objects.select_related("company", "property").prefetch_related("areas").order_by("-created_at")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["can_create"] = True
        if not user.is_superuser and user.company_id:
            try:
                sub = ensure_module_access(company_id=user.company_id, module_key="guarantees")
                lim = get_limit(sub, "limits.max_guarantees")
                if lim is not None and self.get_queryset().count() >= lim:
                    ctx["can_create"] = False
            except PermissionError:
                ctx["can_create"] = False
        return ctx


class GuaranteeCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/guarantees/form.html"
    active_nav = "guarantees"

    def get_form(self):
        cid = self.company_id()
        form = GuaranteeForm()
        def _label(p):
            return str(p)

        form.fields["property"].label_from_instance = _label
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["principal_area"].queryset = form.fields["principal_area"].queryset.filter(property__company_id=cid)
            form.fields["business_partner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
            form.fields["currency"].queryset = Currency.objects.filter(company_id=cid, is_active=True).order_by("code")
            form.fields["product"].queryset = ProductionProduct.objects.filter(company_id=cid, is_active=True).order_by("name")
        return form

    def get(self, request, *args, **kwargs):
        cid = self.company_id()
        props = Property.objects.select_related("owner").filter(company_id=cid).order_by("description") if cid is not None else Property.objects.none()
        areas = Area.objects.filter(property__company_id=cid).order_by("matricula") if cid is not None else Area.objects.none()
        property_owner = {str(p.id): (p.owner.name if p.owner else "") for p in props}
        areas_by_property = {}
        for a in areas:
            areas_by_property.setdefault(str(a.property_id), []).append({"id": a.id, "matricula": a.matricula})
        return self.render_to_response(
            {
                "form": self.get_form(),
                "active_nav": self.active_nav,
                "mode": "create",
                "property_owner_json": json.dumps(property_owner),
                "areas_by_property_json": json.dumps(areas_by_property),
            }
        )

    def post(self, request, *args, **kwargs):
        cid = self.company_id()
        form = GuaranteeForm(request.POST)
        form.fields["property"].label_from_instance = lambda p: str(p)
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["principal_area"].queryset = form.fields["principal_area"].queryset.filter(property__company_id=cid)
            form.fields["business_partner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
            form.fields["currency"].queryset = Currency.objects.filter(company_id=cid, is_active=True).order_by("code")
            form.fields["product"].queryset = ProductionProduct.objects.filter(company_id=cid, is_active=True).order_by("name")
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            # Produto (dropdown simples) -> grava como lista de produtos (M2M)
            prod = form.cleaned_data.get("product")
            if prod:
                obj.products.set([prod])
            else:
                obj.products.clear()
            # Matrícula principal também vira o vínculo de áreas (evita duplicidade no formulário)
            if obj.principal_area_id:
                obj.areas.set([obj.principal_area_id])
            messages.success(request, "Garantia criada com sucesso.")
            return redirect("app_guarantees_list")
        props = Property.objects.select_related("owner").filter(company_id=cid).order_by("description") if cid is not None else Property.objects.none()
        areas = Area.objects.filter(property__company_id=cid).order_by("matricula") if cid is not None else Area.objects.none()
        property_owner = {str(p.id): (p.owner.name if p.owner else "") for p in props}
        areas_by_property = {}
        for a in areas:
            areas_by_property.setdefault(str(a.property_id), []).append({"id": a.id, "matricula": a.matricula})
        return self.render_to_response(
            {
                "form": form,
                "active_nav": self.active_nav,
                "mode": "create",
                "property_owner_json": json.dumps(property_owner),
                "areas_by_property_json": json.dumps(areas_by_property),
            }
        )


class GuaranteeUpdateView(CompanyScopedMixin, TemplateView):
    template_name = "app/guarantees/form.html"
    active_nav = "guarantees"

    def get_object(self):
        cid = self.company_id()
        qs = Guarantee.objects.all().select_related("property")
        if cid is not None:
            qs = qs.filter(company_id=cid)
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get_form(self, obj):
        cid = self.company_id()
        form = GuaranteeForm(instance=obj)
        def _label(p):
            return str(p)

        form.fields["property"].label_from_instance = _label
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["principal_area"].queryset = form.fields["principal_area"].queryset.filter(property__company_id=cid)
            form.fields["business_partner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
            form.fields["currency"].queryset = Currency.objects.filter(company_id=cid, is_active=True).order_by("code")
            form.fields["product"].queryset = ProductionProduct.objects.filter(company_id=cid, is_active=True).order_by("name")
            # inicial: pega primeiro produto se existir
            first_prod = obj.products.first()
            if first_prod:
                form.initial["product"] = first_prod.pk
        return form

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        cid = self.company_id()
        props = Property.objects.select_related("owner").filter(company_id=cid).order_by("description") if cid is not None else Property.objects.none()
        areas = Area.objects.filter(property__company_id=cid).order_by("matricula") if cid is not None else Area.objects.none()
        property_owner = {str(p.id): (p.owner.name if p.owner else "") for p in props}
        areas_by_property = {}
        for a in areas:
            areas_by_property.setdefault(str(a.property_id), []).append({"id": a.id, "matricula": a.matricula})
        return self.render_to_response(
            {
                "form": self.get_form(obj),
                "active_nav": self.active_nav,
                "mode": "edit",
                "obj": obj,
                "property_owner_json": json.dumps(property_owner),
                "areas_by_property_json": json.dumps(areas_by_property),
            }
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        cid = self.company_id()
        # Plano por matrícula: após primeira impressão, bloquear alterações.
        if not request.user.is_superuser and cid is not None:
            try:
                sub = ensure_module_access(company_id=cid, module_key="guarantees")
                if sub.is_locked:
                    messages.error(
                        request,
                        "Plano travado após a primeira impressão; não é permitido alterar a garantia.",
                    )
                    return redirect("app_guarantees_list")
            except PermissionError:
                messages.error(request, "Acesso bloqueado: trial expirado ou assinatura inativa.")
                return redirect("app_guarantees_list")
        form = GuaranteeForm(request.POST, instance=obj)
        form.fields["property"].label_from_instance = lambda p: str(p)
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["principal_area"].queryset = form.fields["principal_area"].queryset.filter(property__company_id=cid)
            form.fields["business_partner"].queryset = BusinessPartner.objects.filter(company_id=cid).order_by("name")
            form.fields["currency"].queryset = Currency.objects.filter(company_id=cid, is_active=True).order_by("code")
            form.fields["product"].queryset = ProductionProduct.objects.filter(company_id=cid, is_active=True).order_by("name")
        if form.is_valid():
            obj = form.save()
            prod = form.cleaned_data.get("product")
            if prod:
                obj.products.set([prod])
            else:
                obj.products.clear()
            if obj.principal_area_id:
                obj.areas.set([obj.principal_area_id])
            messages.success(request, "Garantia atualizada.")
            return redirect("app_guarantees_list")
        props = Property.objects.select_related("owner").filter(company_id=cid).order_by("description") if cid is not None else Property.objects.none()
        areas = Area.objects.filter(property__company_id=cid).order_by("matricula") if cid is not None else Area.objects.none()
        property_owner = {str(p.id): (p.owner.name if p.owner else "") for p in props}
        areas_by_property = {}
        for a in areas:
            areas_by_property.setdefault(str(a.property_id), []).append({"id": a.id, "matricula": a.matricula})
        return self.render_to_response(
            {
                "form": form,
                "active_nav": self.active_nav,
                "mode": "edit",
                "obj": obj,
                "property_owner_json": json.dumps(property_owner),
                "areas_by_property_json": json.dumps(areas_by_property),
            }
        )