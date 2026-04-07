from django.contrib import admin

from .models import Commitment, CropSeason


@admin.register(CropSeason)
class CropSeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "start_date", "end_date")
    list_filter = ("company",)


@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ("id", "guarantee", "crop_season", "value", "created_at")
    list_filter = ("crop_season__company",)
