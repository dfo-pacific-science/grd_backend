import django_filters as filters

from grd.models import Individual

from .queries import FAILED_RESULTS, RESULT_TYPES


# Comma-separated lists, e.g. ?species=124,125. Each value is checked by the base filter,
# so a bad value is a 400 rather than a database error.
class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class ChoiceInFilter(filters.BaseInFilter, filters.ChoiceFilter):
    pass


class IndividualFilter(filters.FilterSet):
    """Filters for the individuals views (4.2.2). Param names are registry terms.

    field_name picks the cheapest SQL for each filter:
    - real columns and F() paths (workbook, pbt) filter on the joined column directly
    - top-1 values (repunit, probability, cu) only exist as subquery annotations
    - inventory fields filter on their annotations, so a filter always matches the value
      shown in the column, even if a fish gets several inventory links later
    Categories are multi-select (in), numbers and dates are ranges (_min/_max), and
    indiv is the only text search.
    """

    # Common (4.4.1)
    indiv = filters.CharFilter(field_name="indiv", lookup_expr="icontains")
    species = NumberInFilter(field_name="workbook__species_id")
    sample_collection = CharInFilter(field_name="sample_collection")
    sample_code = CharInFilter(field_name="sample_code")
    catch_year = filters.RangeFilter(field_name="catch_year")
    catch_date_min = filters.DateFilter(field_name="catch_date", lookup_expr="gte")
    catch_date_max = filters.DateFilter(field_name="catch_date", lookup_expr="lte")
    # result_type and failed_result are both stored in id_source (4.4.4). The choices stop
    # a failure reason being sent as a result type, and the reverse.
    result_type = ChoiceInFilter(
        field_name="id_source", choices=[(v, v) for v in RESULT_TYPES]
    )

    # Analysis (4.4.2). Workbook is sent as its numeric ID (1.6).
    workbook = NumberInFilter(field_name="workbook")

    # Results (4.4.3)
    repunit = CharInFilter(field_name="repunit")
    probability = filters.RangeFilter(field_name="probability")
    top_collection = CharInFilter(field_name="top_collection")
    top_collection_probability = filters.RangeFilter(field_name="top_collection_probability")
    cu = CharInFilter(field_name="cu")
    pbt_brood_year = filters.RangeFilter(field_name="pbt__pbt_brood_year")
    pbt_brood_collection = CharInFilter(field_name="pbt__pbt_brood_collection")
    sex_id = CharInFilter(field_name="sex_id")
    failed_result = ChoiceInFilter(
        field_name="id_source", choices=[(v, v) for v in FAILED_RESULTS]
    )

    class Meta:
        model = Individual
        # Every filter is declared above, so param names are always registry terms.
        fields = []
