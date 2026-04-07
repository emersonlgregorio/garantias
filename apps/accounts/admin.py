from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Company, User


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "saas_plans", "plan", "status", "created_at")
    search_fields = ("name", "cnpj")

    def saas_plans(self, obj: Company) -> str:
        # Import tardio para evitar acoplamento no admin.
        from apps.billing.models import Subscription

        subs = (
            Subscription.objects.select_related("module", "plan")
            .filter(company_id=obj.pk)
            .order_by("module__name")
        )
        parts = []
        for s in subs:
            mod = s.module.name if s.module else "—"
            parts.append(f"{mod}: {s.plan.name}")
        return " | ".join(parts) if parts else "—"

    saas_plans.short_description = "Planos (SaaS)"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "company", "role", "is_staff", "is_active")
    search_fields = ("email",)
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("company", "role", "first_name", "last_name")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "company", "role", "password1", "password2", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )
