"""Models for the `grd` schema — the core genetic stock ID dataset.

Every model is ``managed = False`` — the ingestion pipeline owns these tables,
Django only reads and writes rows, never runs DDL. Table names are unqualified
and resolve through the connection ``search_path`` (see POSTGRES_SEARCH_PATH).

Lookup tables live in the ``grd_ref`` app; validation tables in ``grd_validation``.
grd rows reference ref values by string (e.g. ``individuals.sex_id``), not by FK.
"""

from django.db import models


class Unmanaged(models.Model):
    class Meta:
        abstract = True
        managed = False
        ordering = ["pk"]


class Project(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    species_id = models.BigIntegerField()
    sha256 = models.BinaryField()
    original_filename = models.TextField()
    ingestion_date = models.DateField()
    pipeline_version = models.CharField(max_length=255, blank=True, null=True)
    date_run = models.DateField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)
    baseline_file = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "projects"
        ordering = ["-ingestion_date", "-id"]

    def __str__(self):
        return f"{self.id}: {self.original_filename}"


class CollectionsAndGroups(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(
        Project, models.DO_NOTHING, db_column="projects_id", related_name="collections"
    )
    group = models.TextField()
    collection = models.TextField(blank=True, null=True)
    collection_display_order = models.BigIntegerField(blank=True, null=True)
    group_display_order = models.BigIntegerField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "collections_and_groups"


class ProjectBaselineFile(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(
        Project, models.DO_NOTHING, db_column="projects_id", related_name="baseline_files"
    )
    repunit = models.TextField()
    collection = models.TextField(blank=True, null=True)
    cu = models.CharField(max_length=255, blank=True, null=True)
    cu_name = models.TextField(blank=True, null=True)
    display_order = models.BigIntegerField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "project_baseline_files"
        ordering = ["display_order", "id"]


class Inventory(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(
        Project, models.DO_NOTHING, db_column="projects_id", related_name="inventories"
    )
    sample_collection = models.TextField()
    sample_code = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    area_fished = models.TextField(blank=True, null=True)
    attributes = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "inventories"
        verbose_name_plural = "inventories"

    def __str__(self):
        return self.sample_collection


class Estimate(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    inventory = models.ForeignKey(
        Inventory, models.DO_NOTHING, db_column="inventories_id", related_name="estimates"
    )
    estimates_type = models.TextField()
    point_estimate = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    standard_deviation = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    lower_credible_interval = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    upper_credible_interval = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    conservation_unit_code = models.TextField(blank=True, null=True)
    conservation_unit_name = models.TextField(blank=True, null=True)
    repunit = models.TextField(blank=True, null=True)
    region = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "estimates"


class Individual(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(
        Project, models.DO_NOTHING, db_column="projects_id", related_name="individuals"
    )
    indiv = models.TextField()
    id_source = models.TextField(blank=True, null=True)
    top_collection = models.TextField(blank=True, null=True)
    top_collection_probability = models.DecimalField(
        max_digits=8, decimal_places=5, blank=True, null=True
    )
    catch_year = models.IntegerField(blank=True, null=True)
    catch_date = models.DateField(blank=True, null=True)
    catch_date_2 = models.DateField(blank=True, null=True)
    mgl_pid = models.TextField(blank=True, null=True)
    mgl_pid_batch = models.TextField(blank=True, null=True)
    sex_id = models.TextField(blank=True, null=True)
    sex_note = models.TextField(blank=True, null=True)
    stamp_id = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals"
        ordering = ["id"]

    def __str__(self):
        return self.indiv


class IndividualCollectionResult(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="collection_results",
    )
    collection = models.TextField()
    probability = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_collection_results"
        ordering = ["-probability"]


class IndividualRepunitResult(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="repunit_results",
    )
    repunit = models.TextField()
    probability = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_repunit_results"
        ordering = ["-probability"]


class IndividualRegionResult(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="region_results",
    )
    region = models.TextField()
    probability = models.DecimalField(max_digits=8, decimal_places=5, blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_region_results"
        ordering = ["-probability"]


class IndividualCustomResult(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="custom_results",
    )
    group = models.TextField()
    probability = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_custom_results"
        ordering = ["-probability"]


class IndividualPbt(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.OneToOneField(
        Individual, models.DO_NOTHING, db_column="individuals_id", related_name="pbt"
    )
    attributes = models.JSONField()
    pbt_brood_year = models.SmallIntegerField(blank=True, null=True)
    pbt_brood_collection = models.TextField(blank=True, null=True)
    pbt_brood_group = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_pbt"


class IndividualExtraction(Unmanaged):
    individual = models.OneToOneField(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        primary_key=True, related_name="extraction",
    )
    attributes = models.JSONField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_extraction"
        ordering = ["individual"]


class IndividualPositiveSpecies(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="positive_species",
    )
    positive_species_id = models.BigIntegerField()
    pos_sp_id = models.IntegerField(blank=True, null=True)
    pos_sp_id_proportion = models.DecimalField(
        max_digits=20, decimal_places=8, blank=True, null=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_positive_species"


class IndividualNegativeSpecies(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="negative_species",
    )
    negative_species_confirmed = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_negative_species"


class IndividualDuplicate(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual_1 = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id_1",
        related_name="duplicates_as_1",
    )
    individual_2 = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id_2",
        related_name="duplicates_as_2",
    )
    num_non_miss = models.IntegerField(blank=True, null=True)
    num_match = models.IntegerField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_duplicates"


class IndividualInventory(Unmanaged):
    id = models.BigAutoField(primary_key=True)
    individual = models.ForeignKey(
        Individual, models.DO_NOTHING, db_column="individuals_id",
        related_name="individual_inventories",
    )
    inventory = models.ForeignKey(
        Inventory, models.DO_NOTHING, db_column="inventories_id",
        related_name="individual_inventories",
    )

    class Meta(Unmanaged.Meta):
        db_table = "individuals_inventories"
        unique_together = (("individual", "inventory"),)


# --- reporting views (read-only; `id` is not guaranteed unique per row) ---


class IndividualRunData(Unmanaged):
    id = models.BigIntegerField(primary_key=True)
    indiv = models.TextField(blank=True, null=True)
    date_run = models.DateField(blank=True, null=True)
    species_id = models.BigIntegerField(blank=True, null=True)
    species = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "individuals_run_data_v"


class InventoryRunData(Unmanaged):
    id = models.BigIntegerField(primary_key=True)
    sample_collection = models.TextField(blank=True, null=True)
    date_run = models.DateField(blank=True, null=True)
    species_id = models.BigIntegerField(blank=True, null=True)
    species = models.TextField(blank=True, null=True)

    class Meta(Unmanaged.Meta):
        db_table = "inventories_run_data_v"
