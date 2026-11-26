import csv
from itertools import batched

from django.db.models import F
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from grd_ref.models import SpeciesRef
from grd_validation.models import MappedTerm

from .field_metadata_stub import DICTIONARY_STUB
from .filters import EstimateFilter, IndividualFilter
from .queries import ID_SOURCE, TOP_N, estimate_summaries, individuals_per_fish, workbooks
from .registry import FIELDS_BY_TERM, INDIVIDUAL_FIELDS, PER_FISH, default_terms
from .serializers import IndividualFieldSerializer

# Public, read-only for the MVP (open question 5). Swap for IsAuthenticated or a custom
# permission when access control lands (E10).
PERMISSION = [AllowAny]


class IndividualsPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 500


def parse_fields(params, view):
    """Turn ?fields=a,b into a list of registry terms available in the given view (4.2.3).

    No fields= returns the view's default columns for the id_source filter (4.15).
    Unknown terms, or terms from the other view, raise a 400 keyed by "fields".
    """
    raw = params.get("fields", "")
    # Drop blanks and duplicates, keeping the requested order.
    cleaned = list(dict.fromkeys(f.strip() for f in raw.split(",") if f.strip()))

    if not cleaned:
        return default_terms(view, params.get("id_source", ""))

    unknown_terms = [term for term in cleaned if term not in FIELDS_BY_TERM]
    # Known terms that only exist in the other view, e.g. rank on the per-fish view.
    wrong_view_terms = [
        term
        for term in cleaned
        if term in FIELDS_BY_TERM and view not in FIELDS_BY_TERM[term].view
    ]

    errors = []
    if unknown_terms:
        errors.append(f"Unknown fields: {', '.join(unknown_terms)}")
    if wrong_view_terms:
        errors.append(
            f"Not available in the {view} view: {', '.join(wrong_view_terms)}"
        )
    if errors:
        raise ValidationError({"fields": errors})

    return cleaned


def parse_ordering(params, view):
    """Turn ?ordering=-catch_year into order_by expressions (4.5).

    One registry term, "-" prefix for descending. Blanks sort last either way, so a
    descending sort doesn't open on a page of empty cells. "id" is the tiebreaker that
    keeps paging stable when many fish share a value. No ordering= keeps indiv order.
    """
    raw = params.get("ordering", "").strip()
    if not raw:
        return [F("indiv").asc(), F("id").asc()]

    descending = raw.startswith("-")
    term = raw.removeprefix("-")
    if term not in FIELDS_BY_TERM or view not in FIELDS_BY_TERM[term].view:
        raise ValidationError({"ordering": [f"Cannot sort by: {term}"]})

    expr = F(term).desc(nulls_last=True) if descending else F(term).asc(nulls_last=True)
    return [expr, F("id").asc()]


def filtered_individuals(request):
    """Return a queryset of individuals filtered by the request's query parameters (4.2.2)."""
    # FilterSet takes the request's query params and returns a filtered queryset.
    # Parse first so a bad fields= fails before any query is built.
    fields = parse_fields(request.query_params, PER_FISH)
    ordering = parse_ordering(request.query_params, PER_FISH)
    filterset = IndividualFilter(request.query_params, queryset=individuals_per_fish())
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs.order_by(*ordering), fields


def export_filename(request):
    """Build e.g. grdb_individuals_chinook_20261112-1430.csv for a CSV download (4.2.4).

    The species name is included only when exactly one species is filtered. Call this after
    filtered_individuals, which has already rejected a malformed species= with a 400.
    """
    parts = ["grdb_individuals"]
    species_ids = [
        s for s in request.query_params.get("species", "").split(",") if s.strip()
    ]
    if len(species_ids) == 1:
        name = (
            SpeciesRef.objects.filter(id=species_ids[0])
            .values_list("value", flat=True)
            .first()
        )
        if name:
            # slugify keeps the name safe inside a header and a filename ("Coho (IF)" -> "coho-if").
            parts.append(slugify(name))
    # localtime follows TIME_ZONE; a naive datetime.now() would ignore it.
    parts.append(timezone.localtime().strftime("%Y%m%d-%H%M"))
    return "_".join(parts) + ".csv"


class Echo:
    """An object that implements just the write method of the file-like interface.

    Used to stream CSV data to the client without buffering it all in memory first.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class IndividualsExportView(APIView):
    """Render a queryset of individuals as CSV, streaming to the client (4.2.4)."""

    permission_classes = PERMISSION

    def get(self, request):
        """Return a response that yields CSV rows for the given queryset and fields."""
        writer = csv.writer(Echo())

        queryset, fields = filtered_individuals(request)
        # get plain values tuples in a set chunk size
        rows = queryset.values_list(*fields).iterator(chunk_size=2000)

        def stream():
            yield writer.writerow(fields)
            for batch in batched(rows, 100):
                yield "".join(writer.writerow(row) for row in batch)

        return StreamingHttpResponse(
            stream(),
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{export_filename(request)}"'
            },
        )


class IndividualsView(APIView):
    """One row per fish, with the requested columns, paginated (4.2.1, 4.2.3)."""

    permission_classes = PERMISSION

    def get(self, request):
        qs, fields = filtered_individuals(request)
        # return only selected columns plus id for table row keys
        qs = qs.values("id", *fields)
        paginator = IndividualsPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(page)


class IndividualFilterOptionsView(APIView):
    """Choices for every select filter on the Individuals page (3.5).

    Takes the same filter params as IndividualsView. Each list comes from the per-fish queryset
    narrowed by every active filter except its own (faceted filtering), so every option still
    matches at least one fish, and picking one value never hides the others in the same list.
    """

    permission_classes = PERMISSION

    # Filters whose options are the distinct values of a per-fish annotation.
    DISTINCT_TERMS = [
        "sample_collection",
        "sample_code",
        "repunit",
        "top_collection",
        "cu",
        "pbt_brood_collection",
        "sex_id",
        "baseline_file",
        "repunits_file",
    ]

    def get(self, request):
        params = request.query_params
        # Validate every filter once up front, so a bad value gets the same 400 as the table.
        check = IndividualFilter(params, queryset=individuals_per_fish())
        if not check.is_valid():
            raise ValidationError(check.errors)

        def facet(term):
            """Fish matching every active filter except term's own."""
            others = params.copy()  # QueryDict is immutable; copy() gives a mutable one
            others.pop(term, None)
            return IndividualFilter(others, queryset=individuals_per_fish()).qs

        options = {
            # ID and name pairs: filters send the ID, the UI shows the name (1.6).
            "species": [
                {"value": s.id, "label": s.value}
                for s in SpeciesRef.objects.filter(
                    id__in=facet("species").values("workbook__species_id")
                ).order_by("value")
            ],
            "workbook": [
                {"value": wid, "label": name}
                for wid, name in facet("workbook")
                .values_list("workbook_id", "original_filename")
                .distinct()
                .order_by("original_filename")
            ],
            "id_source": ID_SOURCE,
        }
        for term in self.DISTINCT_TERMS:
            options[term] = list(
                facet(term)
                .exclude(**{f"{term}__isnull": True})
                .values_list(term, flat=True)
                .distinct()
                .order_by(term)
            )
        return Response(options)


class IndividualFieldsView(APIView):
    """Individuals page fields in registry order, with labels and definitions from the dictionary (3.3)."""

    permission_classes = PERMISSION

    @extend_schema(responses=IndividualFieldSerializer(many=True))
    def get(self, request):
        # Look up by dictionary term, which differs from the API term for a few lookups like species.
        queryset = MappedTerm.objects.filter(
            term__in=[f.lookup_term for f in INDIVIDUAL_FIELDS]
        )
        # Build a dict {dictionary term: mapped_term} for quick lookup.
        by_term = {mt.term: mt for mt in queryset}

        # Loop over INDIVIDUAL_FIELDS in order and build one dict per field. Dictionary values come
        # from mapped_terms when the term is loaded, otherwise from the stub (until 3.1).
        field_dicts = []
        for field in INDIVIDUAL_FIELDS:
            mapped_term = by_term.get(field.lookup_term)
            stub = DICTIONARY_STUB.get(field.term, {})
            field_dicts.append(
                {
                    "term": field.term,
                    # "or" also falls back when the dictionary row exists but the value is blank.
                    "label": (mapped_term and mapped_term.frontend_term)
                    or stub.get("label"),
                    "definition": (mapped_term and mapped_term.definition)
                    or stub.get("definition"),
                    "original_workbook_term": (
                        mapped_term.original_workbook_term if mapped_term else None
                    ),
                    "group": field.group,
                    "default_for": sorted(field.default_for),
                    "views": sorted(field.view),
                }
            )
        return Response(IndividualFieldSerializer(field_dicts, many=True).data)


# Workbooks (2.5) ----------------------------------------------------------------------

# Columns of the Workbooks list, in display order. Each name must be a model field or an
# annotation in workbooks(); .values() raises an error for anything else.
WORKBOOK_FIELDS = [
    "id",
    "original_filename",
    "date_run",
    "ingestion_date",
    "pipeline_version",
    "baseline_file",
    # TODO (Frazer): add each annotation from workbooks() here as you write it.
]


class WorkbooksView(APIView):
    """Every workbook, one row each, unpaginated (2.5).

    Small table (31 rows), so the frontend does search, sort and filtering in the browser.
    Shape matches the estimates endpoint: {count, results}.
    """

    permission_classes = PERMISSION

    def get(self, request):
        rows = list(workbooks().values(*WORKBOOK_FIELDS))
        return Response({"count": len(rows), "results": rows})


# Stock proportion estimates (E5) ------------------------------------------------------

ESTIMATE_SUMMARY_FIELDS = [
    "id",
    "workbook_id",
    "original_filename",
    "species",
    "sample_collection",
    "sample_code",
    "pid",
    "year",
    "n_reported",
    "n_failed",
]


def filtered_estimate_summaries(params):
    """estimate_summaries() narrowed by EstimateFilter, or a 400 for a bad value."""
    filterset = EstimateFilter(params, queryset=estimate_summaries())
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs


class EstimatesView(APIView):
    """Compact estimates summary: one row per selected sample collection (5.2, 5.4, 5.7).

    Requires ?species= and at least one of ?workbook= or ?sample_collection=, so a request
    can never span species or the whole database. Rows are listed side by side and never
    summed, averaged or recalculated. sd and credible intervals are never returned (5.3).
    """

    permission_classes = PERMISSION

    def get(self, request):
        params = request.query_params
        errors = {}
        if not params.get("species"):
            errors["species"] = ["Select a species first."]
        if not (params.get("workbook") or params.get("sample_collection")):
            errors["selection"] = ["Select at least one workbook or sample collection."]
        if errors:
            raise ValidationError(errors)

        top_fields = [f"{kind}_{n}" for n in range(1, TOP_N + 1) for kind in ("repunit", "estimate")]
        rows = filtered_estimate_summaries(params).values(*ESTIMATE_SUMMARY_FIELDS, *top_fields)

        results = []
        for row in rows:
            # Flat repunit_1/estimate_1 ... columns become one list, highest first. Missing
            # ranks (fewer than TOP_N repunits, or no estimates at all) are left out.
            top = [
                {"repunit": row.pop(f"repunit_{n}"), "estimate": row.pop(f"estimate_{n}")}
                for n in range(1, TOP_N + 1)
            ]
            row["top_repunits"] = [t for t in top if t["repunit"] is not None]
            results.append(row)
        return Response({"count": len(results), "results": results})


class EstimateFilterOptionsView(APIView):
    """Choices for the estimates query bar (5.1), faceted like the individuals filters.

    species lists every species with inventories. workbook and sample_collection only list
    choices for the selected species, each narrowed by the other selection.
    """

    permission_classes = PERMISSION

    # Filters whose options are the distinct values of an estimate_summaries() annotation.
    # pid, year and the counts are typed (contains match or From/To), so they have no list.
    DISTINCT_TERMS = ["sample_collection", "sample_code"]

    def get(self, request):
        params = request.query_params
        # Validate once up front, so a bad value (year_min=abc is fine as text, but
        # n_reported_min=abc is not) gets a 400 instead of being silently dropped.
        check = EstimateFilter(params, queryset=estimate_summaries())
        if not check.is_valid():
            raise ValidationError(check.errors)

        def facet(term):
            """Inventories matching every active selection except term's own."""
            others = params.copy()
            others.pop(term, None)
            return filtered_estimate_summaries(others)

        species_ids = estimate_summaries().values("workbook__species_id")
        options = {
            "species": [
                {"value": s.id, "label": s.value}
                for s in SpeciesRef.objects.filter(id__in=species_ids).order_by("value")
            ],
            "workbook": [],
            # Same keys before and after a species is picked, so the frontend type always holds.
            **{term: [] for term in self.DISTINCT_TERMS},
        }
        # No species yet: only the species list, so species are never mixed (5.1).
        if params.get("species"):
            options["workbook"] = [
                {"value": wid, "label": name}
                for wid, name in facet("workbook")
                .values_list("workbook_id", "original_filename")
                .distinct()
                .order_by("original_filename")
            ]
            for term in self.DISTINCT_TERMS:
                options[term] = list(
                    facet(term)
                    # Blank sample codes would show as an empty choice.
                    .exclude(**{f"{term}__isnull": True})
                    .order_by()
                    .values_list(term, flat=True)
                    .distinct()
                    .order_by(term)
                )
        return Response(options)
