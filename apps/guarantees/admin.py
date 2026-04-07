from django.contrib import admin

from .models import Guarantee, GuaranteeArea


class GuaranteeAreaInline(admin.TabularInline):
    model = GuaranteeArea
    extra = 0


@admin.register(Guarantee)
class GuaranteeAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "property", "crop_season", "company", "status", "issue_date")
    list_filter = ("type", "company", "status")
    inlines = [GuaranteeAreaInline]


@admin.register(GuaranteeArea)
class GuaranteeAreaAdmin(admin.ModelAdmin):
    list_display = ("guarantee", "area", "created_at")
