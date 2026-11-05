from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .queries import individuals_per_fish
from grd_validation.models import MappedTerm

from .field_metadata_stub import DICTIONARY_STUB
from .registry import INDIVIDUAL_FIELDS
from .serializers import IndividualFieldSerializer
from rest_framework.pagination import PageNumberPagination

# Public, read-only for the MVP (open question 5). Swap for IsAuthenticated or a custom
# permission when access control lands (E10).
PERMISSION = [AllowAny]


class IndividualsPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 500


class IndividualsView(APIView):
    permission_classes = PERMISSION

    def get(self, request):
        queryset = individuals_per_fish().order_by("indiv", "id")
        rows = queryset.values(
            "id",
            "indiv",
            "species",
            "sample_collection",
            "sample_code",
            "catch_date",
            "catch_year",
            "result_type",
            "workbook_name",
            "repunit",
            "probability",
            "top_collection",
            "top_collection_probability",
            "cu",
            "cu_name",
            "pbt_brood_year",
            "pbt_brood_collection",
            "sex_id",
            "failed_result",
        )
        paginator = IndividualsPagination()
        paginated_rows = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(paginated_rows)


class IndividualFieldsView(APIView):
    """Individuals page fields in registry order, with labels and definitions from the dictionary (3.3)."""

    permission_classes = PERMISSION

    @extend_schema(responses=IndividualFieldSerializer(many=True))
    def get(self, request):
        queryset = MappedTerm.objects.filter(
            term__in=[f.term for f in INDIVIDUAL_FIELDS]
        )
        # Build a dict {term: mapped_term} for quick lookup.
        by_term = {mt.term: mt for mt in queryset}

        # Loop over INDIVIDUAL_FIELDS in order and build one dict per field. Dictionary values come
        # from mapped_terms when the term is loaded, otherwise from the stub (until 3.1).
        field_dicts = []
        for field in INDIVIDUAL_FIELDS:
            mapped_term = by_term.get(field.term)
            stub = DICTIONARY_STUB.get(field.term, {})
            field_dicts.append(
                {
                    "term": field.term,
                    "label": (
                        mapped_term.frontend_term if mapped_term else stub.get("label")
                    ),
                    "definition": (
                        mapped_term.definition
                        if mapped_term
                        else stub.get("definition")
                    ),
                    "original_workbook_term": (
                        mapped_term.original_workbook_term if mapped_term else None
                    ),
                    "group": field.group,
                    "default_visible": field.default_visible,
                    "views": sorted(field.view),
                }
            )

        return Response(IndividualFieldSerializer(field_dicts, many=True).data)
