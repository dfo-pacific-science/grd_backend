"""Report endpoints — ports of the Next.js `app/api/*` routes.

Same query params and same `{data, page, pageSize, total, totalPages}` envelope
as the originals; the `<name>/download/` variant returns the bare row array
(page forced to "all", JSONB columns flattened) for client-side Excel export.

These match the documented public API (see the frontend's /apiPage) which is
unauthenticated, so they are `AllowAny`. Flip `PERMISSION` below to lock them.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from . import sql

PERMISSION = [AllowAny]

_QUERY_PARAMS = [
    "page", "sort", "dir", "filter", "species", "idSource",
    "dateFrom", "dateTo", "probabilityMin", "probabilityMax", "year", "sampleCode",
]
_envelope_schema = extend_schema(
    parameters=[
        OpenApiParameter(p, OpenApiTypes.STR, OpenApiParameter.QUERY) for p in _QUERY_PARAMS
    ],
    responses=OpenApiTypes.OBJECT,
)
_array_schema = extend_schema(responses=OpenApiTypes.OBJECT)


def _parse(request) -> dict:
    g = request.query_params.get
    page_raw = (g("page") or "all").strip()
    if page_raw == "all":
        page = "all"
    else:
        page = int(page_raw) if page_raw.lstrip("-").isdigit() else 1
        page = max(1, page)
    return {
        "page": page,
        "sort": g("sort") or "",
        "dir": "desc" if g("dir") == "desc" else "asc",
        "filter": g("filter") or "",
        "species": [int(x) for x in (g("species") or "").split(",") if x.strip().isdigit()],
        "date_from": g("dateFrom") or "",
        "date_to": g("dateTo") or "",
        "id_sources": [x for x in (g("idSource") or "").split(",") if x.strip()],
        "probability_min": g("probabilityMin") or "",
        "probability_max": g("probabilityMax") or "",
        "years": [x for x in (g("year") or "").split(",") if x.strip()],
        "sample_codes": [x for x in (g("sampleCode") or "").split(",") if x.strip()],
    }


def _make_views(name):
    @_envelope_schema
    @api_view(["GET"])
    @permission_classes(PERMISSION)
    def report(request, _name=name):
        return Response(sql.run_report(_name, _parse(request)))

    @_array_schema
    @api_view(["GET"])
    @permission_classes(PERMISSION)
    def download(request, _name=name):
        return Response(sql.run_report(_name, _parse(request), download=True))

    report.__name__ = f"{name}_report"
    download.__name__ = f"{name}_download"
    return report, download


individuals, individuals_download = _make_views("individuals")
bsci_dna_results, bsci_dna_results_download = _make_views("bsciDNAResults")
sc_bdwr_dna, sc_bdwr_dna_download = _make_views("scBDWRDNA")
estimate_catch_by_stock_age, estimate_catch_by_stock_age_download = _make_views(
    "estimateCatchByStockAge"
)
projects, projects_download = _make_views("projects")
sample_collections, sample_collections_download = _make_views("sampleCollections")
stock_proportion_estimates, stock_proportion_estimates_download = _make_views(
    "stockProportionEstimates"
)
data_load, data_load_download = _make_views("dataLoad")


@_array_schema
@api_view(["GET"])
@permission_classes(PERMISSION)
def options_species(request):
    return Response(sql.option_species())


@_array_schema
@api_view(["GET"])
@permission_classes(PERMISSION)
def options_id_sources(request):
    return Response(sql.option_id_sources())


@_array_schema
@api_view(["GET"])
@permission_classes(PERMISSION)
def options_years(request):
    return Response(sql.option_years())


@_array_schema
@api_view(["GET"])
@permission_classes(PERMISSION)
def options_sample_codes(request):
    return Response(sql.option_sample_codes())
