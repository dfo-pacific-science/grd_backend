from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from grd_validation.models import MappedTerm

from .field_metadata_stub import DICTIONARY_STUB
from .registry import INDIVIDUAL_FIELDS
from .serializers import IndividualFieldSerializer

# Public, read-only for the MVP (open question 5). Swap for IsAuthenticated or a custom
# permission when access control lands (E10).
PERMISSION = [AllowAny]


class IndividualFieldsView(APIView):
    """Individuals page fields in registry order, with labels and definitions from the dictionary (3.3)."""

    permission_classes = PERMISSION

    @extend_schema(responses=IndividualFieldSerializer(many=True))
    def get(self, request):
        queryset = MappedTerm.objects.filter(
            term__in=[f.term for f in INDIVIDUAL_FIELDS]
        ).prefetch_related("raw_terms")
        # Build a dict {term: mapped_term} for quick lookup.
        by_term = {mt.term: mt for mt in queryset}

        # Loop over INDIVIDUAL_FIELDS in order and build one dict per field. Dictionary values come
        # from mapped_terms when the term is loaded, otherwise from the stub (until 3.1).
        field_dicts = []
        for field in INDIVIDUAL_FIELDS:
            mapped_term = by_term.get(field.term)
            stub = DICTIONARY_STUB.get(field.term, {})
            field_dicts.append({
                "term": field.term,
                # TODO 3.1: mapped_term.label once mapped_terms has a label column
                "label": stub.get("label"),
                "definition": (mapped_term.definition if mapped_term else None) or stub.get("definition"),
                "workbook_terms": (
                    [rt.term for rt in mapped_term.raw_terms.all()] if mapped_term else []
                ) or stub.get("workbook_terms", []),
                "group": field.group,
                "default_visible": field.default_visible,
                "views": sorted(field.view),
            })

        return Response(IndividualFieldSerializer(field_dicts, many=True).data)
