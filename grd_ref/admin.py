from django.contrib import admin

from . import models

for model in (
    models.AdiposeRef,
    models.EstimatesTypeRef,
    models.GearRef,
    models.IdTypeRef,
    models.SexRef,
    models.SpeciesRef,
):
    admin.site.register(
        model, list_display=("id", "value"), search_fields=("value",), ordering=("value",)
    )
