from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Area, Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("description", "city", "company", "created_at")
    list_filter = ("company",)
    search_fields = ("description", "city")


@admin.register(Area)
class AreaAdmin(GISModelAdmin):
    list_display = ("matricula", "property", "hectares", "created_at")
    list_filter = ("property__company",)
