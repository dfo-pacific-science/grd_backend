"""Models for the `grd_ref` schema — small lookup tables.

`managed = False`: the ingestion pipeline owns these tables. grd rows reference
these by their `value` string, not by a foreign key.
"""

from django.db import models


class RefTable(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.TextField(unique=True)

    class Meta:
        abstract = True
        managed = False
        ordering = ["value"]

    def __str__(self):
        return self.value


class AdiposeRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "adipose_ref"


class EstimatesTypeRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "estimates_type_ref"


class GearRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "gear_ref"


class IdTypeRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "id_type_ref"


class SexRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "sex_ref"


class SpeciesRef(RefTable):
    class Meta(RefTable.Meta):
        db_table = "species_ref"
