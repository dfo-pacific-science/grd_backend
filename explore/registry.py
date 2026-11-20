# a short backend list of the dictionary terms the Individuals page offers.
# Each term has a field group and a default visibility,
# and it holds no labels or definitions.

# It has five jobs:
# Order: set the order of the column picker and table columns (via the metadata endpoint, 3.3).
# Validate: let the fields= parameter be checked (4.2.3). Is this term allowed?
# Defaults: say which columns are shown when no fields= is given.
# Grouping: say which columns are grouped together in the column picker.
# View: which individuals view (per fish or per repunit assignment, 4.14) the field is available in.
#   Used to filter the column picker and to check fields= for the requested view.

# term is the API name: the fields= value, the response key and the queryset annotation.
# Dictionary terms (grd_validation.mapped_terms.term) are database field names. When the
# two differ, dictionary_term points at the dictionary row (e.g. species -> species_ref.value).
# Derived terms with no dictionary row (labels from the stub): rank,
# fish_age, dad_id, mum_id.

from dataclasses import dataclass

PER_FISH = "per_fish"
PER_ASSIGNMENT = "per_assignment"
BOTH_VIEWS = frozenset([PER_FISH, PER_ASSIGNMENT])

# Default columns differ by id_source group (4.15, Shaorong's fields and default columns doc):
# GSI, PBT, or FAILED for the four failure values. A field lists the groups it is a default
# column for; empty means selectable only.
GSI = "GSI"
PBT = "PBT"
FAILED = "FAILED"
BOTH_TYPES = frozenset([GSI, PBT])
ALL_GROUPS = frozenset([GSI, PBT, FAILED])


@dataclass(frozen=True)
class RegistryField:
    term: str
    group: str
    view: frozenset[str] = BOTH_VIEWS
    default_for: frozenset[str] = frozenset()
    dictionary_term: str | None = None  # mapped_terms.term, when it differs from term

    @property
    def lookup_term(self):
        """The mapped_terms.term holding this field's label and definition."""
        return self.dictionary_term or self.term


# Same three groups as the filter panel (4.4, Shaorong's filter requirements).
COMMON = "Common"
ANALYSIS = "Analysis"
RESULTS = "Results"

# Registry order is column order. The leading columns follow the order in Shaorong's doc.
INDIVIDUAL_FIELDS = (
    RegistryField("indiv", COMMON, default_for=ALL_GROUPS),
    RegistryField(
        "species",
        COMMON,
        default_for=ALL_GROUPS,
        dictionary_term="species_ref.value",
    ),
    RegistryField("original_filename", ANALYSIS),
    RegistryField("id_source", COMMON, default_for=ALL_GROUPS),
    RegistryField("sample_collection", ANALYSIS, default_for=ALL_GROUPS),
    RegistryField("sample_code", COMMON),
    RegistryField("catch_date", COMMON),
    RegistryField("catch_year", COMMON, default_for=ALL_GROUPS),
    RegistryField(
        "rank", RESULTS, view=frozenset([PER_ASSIGNMENT]), default_for=frozenset([GSI])
    ),
    # PBT fish have one repunit and top collection, assigned at 100%, so probability is GSI only.
    RegistryField("repunit", RESULTS, default_for=BOTH_TYPES),
    RegistryField("probability", RESULTS, default_for=frozenset([GSI])),
    RegistryField("top_collection", RESULTS, default_for=BOTH_TYPES),
    RegistryField("top_collection_probability", RESULTS),
    RegistryField("cu", RESULTS),
    RegistryField("cu_name", RESULTS),
    RegistryField("pbt_brood_year", RESULTS, default_for=frozenset([PBT])),
    RegistryField("pbt_brood_collection", RESULTS),
    # Parent IDs (4.16), blank where the lab did not provide them.
    RegistryField("dad_id", RESULTS, default_for=frozenset([PBT])),
    RegistryField("mum_id", RESULTS, default_for=frozenset([PBT])),
    RegistryField("sex_id", RESULTS),
    RegistryField("fish_age", RESULTS),
)

def id_source_groups(id_source):
    """Default-column groups for the id_source filter value (single-select, one value or none).

    GSI and PBT are their own groups; the four failure values share FAILED; no value gives
    every group. The frontend twin is idSourceGroups in lib/idSourceGroups.ts: change both.
    """
    if not id_source:
        return ALL_GROUPS
    if id_source in BOTH_TYPES:
        return {id_source}
    return {FAILED}


def default_terms(view, id_source):
    """Default columns for a view and the id_source filter value (4.15).

    A field is a default when its default_for shares a group with the request, e.g. with
    "Too few loci" (FAILED): indiv {GSI, PBT, FAILED} is shown, repunit {GSI, PBT} is not.
    No value gives every group, so the union of all defaults.
    """
    groups = id_source_groups(id_source)
    # & is set intersection: non-empty (truthy) when the field and the request share a group.
    return [f.term for f in INDIVIDUAL_FIELDS if view in f.view and f.default_for & groups]


FIELDS_BY_TERM = {f.term: f for f in INDIVIDUAL_FIELDS}
