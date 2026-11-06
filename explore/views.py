from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from grd_validation.models import MappedTerm

from .field_metadata_stub import DICTIONARY_STUB
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
        return [f.term for f in INDIVIDUAL_FIELDS if f.default_visible and view in f.view]

    unknown_terms = [term for term in cleaned if term not in FIELDS_BY_TERM]
    # Known terms that only exist in the other view, e.g. rank on the per-fish view.
    wrong_view_terms = [
        term for term in cleaned if term in FIELDS_BY_TERM and view not in FIELDS_BY_TERM[term].view
    ]

    errors = []
    if unknown_terms:
        errors.append(f"Unknown fields: {', '.join(unknown_terms)}")
    if wrong_view_terms:
        errors.append(f"Not available in the {view} view: {', '.join(wrong_view_terms)}")
    if errors:
        raise ValidationError({"fields": errors})

    return cleaned


class IndividualsView(APIView):
    """One row per fish, with the requested columns, paginated (4.2.1, 4.2.3)."""

    permission_classes = PERMISSION

    def get(self, request):
        # Parse first so a bad fields= fails before any query is built.
        fields = parse_fields(request.query_params, PER_FISH)
        # "id" breaks ties between re-run fish that share an indiv.
        rows = individuals_per_fish().order_by("indiv", "id").values("id", *fields)
        paginator = IndividualsPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
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
                    "label": (mapped_term and mapped_term.frontend_term) or stub.get("label"),
                    "definition": (mapped_term and mapped_term.definition) or stub.get("definition"),
                    "original_workbook_term": (
                        mapped_term.original_workbook_term if mapped_term else None
                    ),
                    "group": field.group,
                    "default_visible": field.default_visible,
                    "views": sorted(field.view),
                }
            )
        return Response(IndividualFieldSerializer(field_dicts, many=True).data)
