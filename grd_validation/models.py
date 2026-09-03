"""Models for the `grd_validation` schema.

`managed = False`: the ingestion / validation pipeline owns these tables.
"""

from django.db import models


class Unmanaged(models.Model):
    class Meta:
        abstract = True
        managed = False
        ordering = ["pk"]


class FileVersion(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    format_name = models.TextField(blank=True, null=True)
    sha256_checksum = models.BinaryField(unique=True)
    date_added = models.DateField()
    comment = models.TextField(blank=True, null=True)
    original_filename = models.TextField(blank=True, null=True)
    sheet_data_loaded = models.BooleanField(blank=True, null=True)
    grd_data_loaded = models.BooleanField(blank=True, null=True)
    issue_indiv_list = models.JSONField(blank=True, null=True)
    issue_inventories_list = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "file_versions"
        ordering = ["-date_added", "-id"]

    def __str__(self):
        return self.original_filename or f"file {self.id}"


class Sheet(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    file = models.ForeignKey(
        FileVersion, models.DO_NOTHING, db_column="file_id", related_name="sheets"
    )
    sheet_name = models.TextField()
    sheet_data = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "sheets"
        unique_together = (("file", "sheet_name"),)

    def __str__(self):
        return self.sheet_name


class MappedTerm(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    term = models.TextField(unique=True)
    definition = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "mapped_terms"
        ordering = ["term"]

    def __str__(self):
        return self.term


class RawTerm(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    term = models.TextField(unique=True)
    definition = models.TextField()
    mapped_term = models.ForeignKey(
        MappedTerm, models.DO_NOTHING, db_column="mapped_terms_id",
        blank=True, null=True, related_name="raw_terms",
    )

    class Meta(Unmanaged.Meta):
        db_table = "raw_terms"
        ordering = ["term"]

    def __str__(self):
        return self.term
