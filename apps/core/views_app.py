from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import TextInput
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from apps.crops.models import CropSeason
from apps.guarantees.models import Guarantee
from apps.properties.models import Property


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
        fields = ["description", "city"]
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


class PropertyCreateView(CompanyScopedMixin, TemplateView):
    template_name = "app/properties/form.html"
    active_nav = "properties"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": PropertyForm(), "active_nav": self.active_nav, "mode": "create"})

    def post(self, request, *args, **kwargs):
        form = PropertyForm(request.POST)
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
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = PropertyForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Fazenda atualizada.")
            return redirect("app_properties_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})


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
    class Meta:
        model = Guarantee
        fields = [
            "property",
            "crop_season",
            "type",
            "value",
            "issue_date",
            "status",
            "areas",
        ]


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
            form.fields["areas"].queryset = form.fields["areas"].queryset.filter(property__company_id=cid)
        return form

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": self.get_form(), "active_nav": self.active_nav, "mode": "create"})

    def post(self, request, *args, **kwargs):
        cid = self.company_id()
        form = GuaranteeForm(request.POST)
        form.fields["property"].label_from_instance = lambda p: str(p)
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["areas"].queryset = form.fields["areas"].queryset.filter(property__company_id=cid)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = request.user.company
            obj.save()
            form.save_m2m()
            messages.success(request, "Garantia criada com sucesso.")
            return redirect("app_guarantees_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "create"})


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
            form.fields["areas"].queryset = form.fields["areas"].queryset.filter(property__company_id=cid)
        return form

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return self.render_to_response({"form": self.get_form(obj), "active_nav": self.active_nav, "mode": "edit", "obj": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        cid = self.company_id()
        form = GuaranteeForm(request.POST, instance=obj)
        form.fields["property"].label_from_instance = lambda p: str(p)
        if cid is not None:
            form.fields["property"].queryset = Property.objects.filter(company_id=cid)
            form.fields["crop_season"].queryset = CropSeason.objects.filter(company_id=cid)
            form.fields["areas"].queryset = form.fields["areas"].queryset.filter(property__company_id=cid)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Garantia atualizada.")
            return redirect("app_guarantees_list")
        return self.render_to_response({"form": form, "active_nav": self.active_nav, "mode": "edit", "obj": obj})