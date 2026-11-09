from django.db.models import Case, F, OuterRef, Subquery, When

from grd.models import (
    BaselineCollection,
    Individual,
    IndividualInventory,
    IndividualRepunitResult,
)
from grd_ref.models import SpeciesRef

# id_source holds both how a fish was assigned and why it failed (4.4.4).
RESULT_TYPES = ["GSI", "PBT"]
FAILED_RESULTS = [
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
            # Each fish gets one of the two; the other is NULL (no default).
            result_type=Case(When(id_source__in=RESULT_TYPES, then=F("id_source"))),
            failed_result=Case(When(id_source__in=FAILED_RESULTS, then=F("id_source"))),
        )
    )
