from django.contrib import admin

from . import models


@admin.register(models.FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "format_name", "date_added",
                    "sheet_data_loaded", "grd_data_loaded")
    list_filter = ("sheet_data_loaded", "grd_data_loaded", "format_name")
    search_fields = ("original_filename", "format_name", "comment")


@admin.register(models.Sheet)
class SheetAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "sheet_name")
    list_select_related = ("file",)
    search_fields = ("sheet_name",)


@admin.register(models.MappedTerm)
class MappedTermAdmin(admin.ModelAdmin):
    list_display = ("id", "term", "definition")
    search_fields = ("term", "definition")


@admin.register(models.RawTerm)
class RawTermAdmin(admin.ModelAdmin):
    list_display = ("id", "term", "mapped_term")
    list_select_related = ("mapped_term",)
    list_filter = ("mapped_term",)
    search_fields = ("term", "definition")
