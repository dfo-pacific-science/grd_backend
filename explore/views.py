import csv
from itertools import batched

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
from .filters import IndividualFilter
from .queries import individuals_per_fish
from .registry import FIELDS_BY_TERM, INDIVIDUAL_FIELDS, PER_FISH
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

    No fields= returns the view's default columns. Unknown terms, or terms from the other
    view, raise a 400 keyed by "fields".
    """
    raw = params.get("fields", "")
    # Drop blanks and duplicates, keeping the requested order.
    cleaned = list(dict.fromkeys(f.strip() for f in raw.split(",") if f.strip()))

    if not cleaned:
        return [
            f.term for f in INDIVIDUAL_FIELDS if f.default_visible and view in f.view
        ]

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


def filtered_individuals(request):
    """Return a queryset of individuals filtered by the request's query parameters (4.2.2)."""
    # FilterSet takes the request's query params and returns a filtered queryset.
    # Parse first so a bad fields= fails before any query is built.
    fields = parse_fields(request.query_params, PER_FISH)
    filterset = IndividualFilter(request.query_params, queryset=individuals_per_fish())
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    qs = filterset.qs
    # "id" breaks ties between re-run fish that share an indiv.
    qs = qs.order_by("indiv", "id")
    return qs, fields


def export_filename(request):
    """Build e.g. grdb_individuals_chinook_20261112-1430.csv for a CSV download (4.2.4).

    The species name is included only when exactly one species is filtered. Call this after
    filtered_individuals, which has already rejected a malformed species= with a 400.
    """
    parts = ["grdb_individuals"]
    species_ids = [s for s in request.query_params.get("species", "").split(",") if s.strip()]
    if len(species_ids) == 1:
        name = SpeciesRef.objects.filter(id=species_ids[0]).values_list("value", flat=True).first()
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
            headers={"Content-Disposition": f'attachment; filename="{export_filename(request)}"'},
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
                    "default_visible": field.default_visible,
                    "views": sorted(field.view),
                }
            )
        return Response(IndividualFieldSerializer(field_dicts, many=True).data)
