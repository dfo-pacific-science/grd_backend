from django.db.models import (
    DecimalField,
    F,
    IntegerField,
    OuterRef,
    Subquery,
    TextField,
    Value,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Extract, Trim
from django.contrib.postgres.aggregates import StringAgg


from grd.models import (
    BaselineCollection,
    Estimate,
    Individual,
    IndividualExtraction,
    IndividualInventory,
    IndividualRepunitResult,
    Inventory,
    Workbook,
)
from grd_ref.models import SpeciesRef

# id_source holds both how a fish was assigned and why it failed (4.4.4).
ID_SOURCE = [
    "GSI",
    "PBT",
    "Too few loci",
    "Failed to amplify",
    "non-target_species",
    "likely_duplicate",
]


def individuals_per_fish():
    """One row per fish, with its top repunit, probability, CU and CU name."""

    # A fish's repunit results, highest probability first. OuterRef("pk") is the
    # fish on the outer row. nulls_last stops Postgres sorting NULL probabilities
    # to the top on DESC, and "id" breaks ties so the result is consistent.
    repunit_results = IndividualRepunitResult.objects.filter(
        individual=OuterRef("pk"),
    ).order_by(F("probability").desc(nulls_last=True), "id")

    # Baseline crosswalk rows for the fish's workbook and top repunit. Several
    # rows match (one per collection), so take the first by display_order.
    # OuterRef("repunit") is the annotation from the first .annotate() below.
    baseline_match = BaselineCollection.objects.filter(
        workbook=OuterRef("workbook"),
        repunit=OuterRef("repunit"),
    ).order_by("display_order", "id")

    # The fish's inventory link. Every fish has one today, but the table allows
    # several, so a subquery keeps fish from being duplicated.
    inventory_link = IndividualInventory.objects.filter(
        individual=OuterRef("pk"),
    ).order_by("id")

    # Workbook.species_id is a plain integer in the model, so look up the name.
    species_name = SpeciesRef.objects.filter(
        id=OuterRef("workbook__species_id"),
    ).values("value")[:1]

    # The Vial key as text (->>). Used twice below: what to join and what to sort by.
    vial_text = KeyTextTransform("Vial", "attributes")
    vials = (
        IndividualExtraction.objects.filter(individual=OuterRef("pk"))
        # group individual extraction rows by individual so that only one row returned by a subquery
        .values("individual")
        .annotate(
            # string aggregation because some fish have multiple vial numbers. Make a semicolon seperated list.
            # ordering keeps the list the same on every request; with distinct=True,
            # Postgres only allows ordering by the value being aggregated.
            vials=StringAgg(vial_text, "; ", distinct=True, ordering=vial_text)
        )
        # only take the vials value for the annotation
        .values("vials")
    )

    return (
        # Single-row relations only: workbook (INNER JOIN) and pbt (LEFT OUTER
        # JOIN, GSI-only fish have no PBT row). Neither adds rows.
        Individual.objects.select_related("workbook", "pbt")
        # Top repunit and its probability. Both reuse repunit_results so they
        # always come from the same result row. [:1] keeps each to one value.
        .annotate(
            repunit=Subquery(repunit_results.values("repunit")[:1]),
            probability=Subquery(repunit_results.values("probability")[:1]),
        )
        # Chained separately so "repunit" exists before baseline_match uses it.
        # NULL when the workbook has no baseline tab (tracker 6.6).
        .annotate(
            cu=Subquery(baseline_match.values("cu")[:1]),
            cu_name=Subquery(baseline_match.values("cu_name")[:1]),
        )
        # The workbook is shown by its dictionary term original_filename. The
        # workbook FK keeps its name so filters can send the numeric ID (1.6).
        .annotate(
            original_filename=F("workbook__original_filename"),
            species=Subquery(species_name),
            sample_collection=Subquery(
                inventory_link.values("inventory__sample_collection")[:1]
            ),
            sample_code=Subquery(inventory_link.values("inventory__sample_code")[:1]),
            pbt_brood_year=F("pbt__pbt_brood_year"),
            pbt_brood_collection=F("pbt__pbt_brood_collection"),
            # Catch Julian day (4.11): day of year, 1 to 366. NULL when catch_date is missing.
            # "doy" becomes Postgres EXTRACT(DOY ...); Django has no named lookup for it.
            catch_jd=Extract("catch_date", "doy"),
            # PBT age (4.12): catch year minus brood year. NULL for fish with no PBT brood
            # year; no external age source is loaded yet.
            fish_age=F("catch_year") - F("pbt__pbt_brood_year"),
            # PBT parent IDs (4.16), stored in individuals_pbt.attributes. NULL when not provided.
            dad_id=KeyTextTransform("dadid", "pbt__attributes"),
            mum_id=KeyTextTransform("mumid", "pbt__attributes"),
            # Analysis metadata from the workbook (4.4.2). Filters only: 5.6 keeps these out
            # of the results table.
            date_run=F("workbook__date_run"),
            baseline_file=F("workbook__baseline_file"),
            # The repunits file name is stored in projects.attributes as {"repunits": "..."}.
            repunits_file=KeyTextTransform("repunits", "workbook__attributes"),
            vial=Subquery(vials),
        )
    )


# Workbooks (2.5) ----------------------------------------------------------------------


def workbooks():
    """One row per workbook for the Workbooks list page (2.5). Workbook-level values only:
    sample collections and fish are on the detail page, not flattened in here.

    31 workbooks today, so the view returns them all and the frontend searches and sorts.
    """
    # TODO (Frazer) 1: species name. Workbook.species_id is a plain integer, not a ForeignKey,
    # so look the name up in SpeciesRef with a Subquery. Copy species_name from
    # estimate_summaries(), then ask: what is the outer row here, and so what should
    # OuterRef point at?

    return (
        Workbook.objects
        # TODO (Frazer) 2: .annotate(...) with
        #   species             the Subquery from TODO 1
        #   repunits_file       attributes key "repunits"
        #   min_snp_count       attributes key "minimum_indiv_SNP_count"
        #   granularity         attributes key "max_granularity_level"
        #   credible_interval   attributes key "credible_interval"
        # Keys are case-sensitive. Leave out git_commit, custom_rollup and smoke.
        #
        # TODO (Frazer) 3 (optional): n_collections, the number of inventories per workbook.
        # Hint: Count over the related_name on Inventory.workbook.
        .order_by("original_filename")
    )


# Stock proportion estimates (E5). Only REPUNITS estimates feed the summary (5.2).
ESTIMATES_TYPE = "REPUNITS"
# How many repunits the compact summary shows per sample collection (open question 12).
TOP_N = 3


def int_attribute(key):
    """An inventories.attributes value as an integer. Values are text, some with
    leading spaces (" 8"), so trim before casting. All 336 rows are numeric today."""
    return Cast(Trim(KeyTextTransform(key, "attributes")), IntegerField())


def estimate_summaries():
    """One row per sample collection (inventory) for the estimates summary (5.2, 5.4).

    Rows are never combined: the same sample collection analysed in two workbooks is two
    inventories, so two rows. The point estimates are percentages (each collection sums to 100).
    """
    species_name = SpeciesRef.objects.filter(
        id=OuterRef("workbook__species_id"),
    ).values("value")[:1]

    return (
        Inventory.objects.select_related("workbook")
        .annotate(
            original_filename=F("workbook__original_filename"),
            species=Subquery(species_name),
            pid=KeyTextTransform("PID", "attributes"),
            # Text on purpose: one inventory has the year "2023-2024".
            year=KeyTextTransform("Year", "attributes"),
            # 5.4: the workbook's "Reported(filtered)", e.g. 57(1), is stored as two keys.
            n_reported=int_attribute("N_reported"),
            n_failed=int_attribute("N_filtered"),
        )
        .annotate(**top_repunits())
        .order_by("original_filename", "sample_collection", "id")
    )



def top_repunits():
    """Annotations for the TOP_N highest REPUNITS point estimates of each inventory:
    repunit_1, estimate_1, ..., repunit_3, estimate_3. NULL when there are fewer.
    """

    repunit_results_ranked = Estimate.objects.filter(
        inventory=OuterRef("pk"),
        estimates_type=ESTIMATES_TYPE,
        point_estimate__gt=0
    ).order_by(F("point_estimate").desc(nulls_last=True), "repunit")

    annotations = {}
    for n in range(1, TOP_N + 1):
        annotations[f"repunit_{n}"] = Subquery(repunit_results_ranked.values("repunit")[n-1: n])
        annotations[f"estimate_{n}"] = Subquery(repunit_results_ranked.values("point_estimate")[n-1:n])
    return annotations
