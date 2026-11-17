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
# Derived terms with no dictionary row (labels from the stub): result_type, rank, failed_result.

from dataclasses import dataclass

PER_FISH = "per_fish"
PER_ASSIGNMENT = "per_assignment"
BOTH_VIEWS = frozenset([PER_FISH, PER_ASSIGNMENT])

@dataclass(frozen=True)
class RegistryField:
    term: str
    group: str
    view: frozenset[str] = BOTH_VIEWS
    default_visible: bool = False
    dictionary_term: str | None = None  # mapped_terms.term, when it differs from term

    @property
    def lookup_term(self):
        """The mapped_terms.term holding this field's label and definition."""
        return self.dictionary_term or self.term

# Same three groups as the filter panel (4.4, Shaorong's filter requirements).
COMMON = "Common"
ANALYSIS = "Analysis"
RESULTS = "Results"

INDIVIDUAL_FIELDS = (
    RegistryField("indiv", COMMON, default_visible=True),
    RegistryField("species", COMMON, default_visible=True, dictionary_term="species_ref.value"),
    RegistryField("sample_collection", COMMON, default_visible=True),
    RegistryField("sample_code", COMMON),
    RegistryField("catch_date", COMMON, default_visible=True),
    RegistryField("catch_year", COMMON, default_visible=True),
    RegistryField("result_type", COMMON),
    RegistryField("original_filename", ANALYSIS, default_visible=True),
    RegistryField("rank", RESULTS, view=frozenset([PER_ASSIGNMENT]), default_visible=True),
    RegistryField("repunit", RESULTS, default_visible=True),
    RegistryField("probability", RESULTS, default_visible=True),
    RegistryField("top_collection", RESULTS, default_visible=True),
    RegistryField("top_collection_probability", RESULTS, default_visible=True),
    RegistryField("cu", RESULTS),
    RegistryField("cu_name", RESULTS, default_visible=True),
    RegistryField("pbt_brood_year", RESULTS),
    RegistryField("pbt_brood_collection", RESULTS),
    RegistryField("sex_id", RESULTS, default_visible=True),
    RegistryField("failed_result", RESULTS),
)

FIELDS_BY_TERM = {f.term: f for f in INDIVIDUAL_FIELDS}
