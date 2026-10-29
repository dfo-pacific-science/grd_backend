from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from grd_validation.models import MappedTerm

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
        queryset = MappedTerm.objects.filter(term__in=[f.term for f in INDIVIDUAL_FIELDS]).prefetch_related("raw_terms")
        # Build a dict {term: mapped_term} for quick lookup.
        by_term = {mt.term: mt for mt in queryset}
        #Loop over INDIVIDUAL_FIELDS in order and build one dict per field.
        field_dicts = []
        for field in INDIVIDUAL_FIELDS:
            mapped_term = by_term.get(field.term)
            if mapped_term:
                field_dict = {
                    "term": field.term,
                    # label not yet implemented E3.1
                    "label": None,    
                    "definition": mapped_term.definition or None,
                    "workbook_terms": [rt.term for rt in mapped_term.raw_terms.all()],
                    "group": field.group,
                    "default_visible": field.default_visible,
                    "views": sorted(field.view),
                }
                field_dicts.append(field_dict)

        data_stub = [
  {
    "term": "indiv",
    "label": "Individual ID",
    "definition": "Individual fish identifier, \"SampleCode_CatchYear_CatchJulDate_Fish number\".",
    "workbook_terms": ["indiv"],
    "group": "Individual",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "species",
    "label": "Species",
    "definition": "Species of the individual fish.",
    "workbook_terms": ["species"],
    "group": "Individual",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "sample_collection",
    "label": "Sample collection",
    "definition": "A unique identifier associated with samples collected and analysed together within the same project, formatted as Source_AreaCode(Year)_Month(MonthName). Multiple sample_collections can exist under each SampleCode.",
    "workbook_terms": ["collection"],
    "group": "Individual",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "sample_code",
    "label": "Sample code",
    "definition": "A numeric code (increasing from 1) assigned to mixture samples, typically representing batches of samples submitted and requested for analysis together. It forms the first part of the \"indiv\" identifier, and is the same as \"StockCode\" in \"extraction_sheet\".",
    "workbook_terms": ["SampleCode"],
    "group": "Individual",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "catch_date",
    "label": "Catch date",
    "definition": "Date the fish was caught (YYYY-MM-DD).",
    "workbook_terms": ["CatchDate..YYYY.MM.DD."],
    "group": "Individual",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "catch_year",
    "label": "Catch year",
    "definition": "Catch year.",
    "workbook_terms": ["year"],
    "group": "Individual",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "workbook",
    "label": "Workbook",
    "definition": "The MGL workbook (Excel file) the results were loaded from, shown by its file name.",
    "workbook_terms": [],
    "group": "Analysis",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "result_type",
    "label": "Result type",
    "definition": "How the fish was assigned to stock: GSI (Genetic Stock Identification) or PBT (Parentage Based Tagging).",
    "workbook_terms": ["id_source"],
    "group": "Results",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "rank",
    "label": "Rank",
    "definition": "Rank of this repunit assignment for the fish, ordered by probability (1 = top assignment).",
    "workbook_terms": ["rank"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment"]
  },
  {
    "term": "repunit",
    "label": "Repunit",
    "definition": "The genetic reporting scale at which the analysis was considered, typically combining rivers or CUs with indistinguishable or poorly distinguished genetic profiles. Repunits often follow Conservation Unit delineation in Canada, and regional groupings in the US, but may be adjusted (as defined on the baseline_collections tab) based on the specific question at-hand and the available mixture sample size.",
    "workbook_terms": ["repunit"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "CU",
    "label": "CU",
    "definition": "For Canada Conservation Unit number code.",
    "workbook_terms": ["CU"],
    "group": "Results",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "CU_NAME",
    "label": "CU name",
    "definition": "For Canada Conservation Unit name, for US genetic group.",
    "workbook_terms": ["CU_NAME"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "probability",
    "label": "Probability",
    "definition": "Statistical confidence value representing the likelihood that the assigned genetic classification (e.g., parentage or reporting unit) is correct.",
    "workbook_terms": ["rep_pofz"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "top_collection",
    "label": "Top collection",
    "definition": "The baseline collection (population) with the highest assignment probability for the fish, when provided by the lab.",
    "workbook_terms": [],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "pbt_brood_year",
    "label": "PBT brood year",
    "definition": "Brood Year of parents to which individual was assigned via PBT.",
    "workbook_terms": ["pbt_brood_year"],
    "group": "Results",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "pbt_brood_collection",
    "label": "PBT brood collection",
    "definition": "The river system, waterbody or location where broodstock individuals are collected for Parentage-Based Tagging (PBT) analysis.",
    "workbook_terms": ["collection"],
    "group": "Results",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "sex_id",
    "label": "Sex",
    "definition": "male / presumed_female / unknown",
    "workbook_terms": ["sex_id"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "fish_age",
    "label": "Age",
    "definition": "Estimated age of the fish in mixture based on assignment to parents of brood years.",
    "workbook_terms": ["age"],
    "group": "Results",
    "default_visible": true,
    "views": ["per_assignment", "per_fish"]
  },
  {
    "term": "failed_result",
    "label": "Failed result",
    "definition": "Reason no stock result was reported: Too few loci, Failed to amplify, Non-target species or Likely duplicate.",
    "workbook_terms": ["id_source"],
    "group": "Results",
    "default_visible": false,
    "views": ["per_assignment", "per_fish"]
  }
]
        #Serialize the list and return a Response.
        return Response(IndividualFieldSerializer(data_stub, many=True).data)
    
