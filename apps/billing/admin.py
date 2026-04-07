from django.contrib import admin

from .models import Invoice, Module, Plan, PlanFeature, Subscription


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("key", "name")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("module", "name", "billing_type", "price", "is_active")
    list_filter = ("module", "billing_type", "is_active")
    search_fields = ("name", "module__name", "module__key")


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ("plan", "key")
    list_filter = ("plan__module",)
    search_fields = ("key", "plan__name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "module",
        "plan",
        "status",
        "trial_end_date",
        "start_date",
        "end_date",
        "is_locked",
    )
    list_filter = ("status", "module", "is_locked")
    search_fields = ("company__name", "plan__name", "module__key")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("company", "subscription", "amount", "status", "due_date", "created_at")
    list_filter = ("status",)
    search_fields = ("company__name",)
