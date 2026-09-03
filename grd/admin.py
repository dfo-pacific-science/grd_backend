"""Register every `grd` model in the admin. These tables are ``managed = False``
— edits here write straight to the live rows. The two `*_run_data_v` database
views are registered read-only.
"""

from django.contrib import admin

from . import models

_VIEWS = {models.IndividualRunData, models.InventoryRunData}


class _ViewAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "species_id", "pipeline_version",
                    "ingestion_date", "date_run")
    list_filter = ("pipeline_version", "species_id", "ingestion_date")
    search_fields = ("original_filename", "baseline_file")


@admin.register(models.Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = ("id", "indiv", "project", "top_collection",
                    "top_collection_probability", "catch_date")
    list_filter = ("id_source", "sex_id", "catch_year")
    search_fields = ("indiv", "mgl_pid", "mgl_pid_batch", "stamp_id")
    list_select_related = ("project",)
    raw_id_fields = ("project",)


@admin.register(models.Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "sample_collection", "sample_code", "project", "contact")
    search_fields = ("sample_collection", "sample_code", "contact", "area_fished")
    list_select_related = ("project",)
    raw_id_fields = ("project",)


for _model in (
    models.CollectionsAndGroups,
    models.ProjectBaselineFile,
    models.Estimate,
    models.IndividualCollectionResult,
    models.IndividualRepunitResult,
    models.IndividualRegionResult,
    models.IndividualCustomResult,
    models.IndividualPbt,
    models.IndividualExtraction,
    models.IndividualPositiveSpecies,
    models.IndividualNegativeSpecies,
    models.IndividualDuplicate,
    models.IndividualInventory,
    models.IndividualRunData,
    models.InventoryRunData,
):
    admin.site.register(_model, _ViewAdmin if _model in _VIEWS else admin.ModelAdmin)
