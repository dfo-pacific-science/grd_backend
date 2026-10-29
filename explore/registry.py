# a short backend list of the dictionary terms the Individuals page offers.
# Each term has a field group and a default visibility,
# and it holds no labels, definitions or database sources.

# It has five jobs:
# Order: set the order of the column picker and table columns (via the metadata endpoint, 3.3).
# Validate: let the fields= parameter be checked (4.2.3). Is this term allowed?
# Defaults: say which columns are shown when no fields= is given.
# Grouping: say which columns are grouped together in the column picker.
# View: which individuals view (per fish or per repunit assignment, 4.14) the field is available in.
#   Used to filter the column picker and to check fields= for the requested view.

# Terms must match grd_validation.mapped_terms.term exactly. Not in the dictionary yet (3.1):
# workbook, top_collection, result_type, failed_result, rank.

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

# Same three groups as the filter panel (4.4, Shaorong's filter requirements).
COMMON = "Common"
ANALYSIS = "Analysis"
RESULTS = "Results"

INDIVIDUAL_FIELDS = (
    RegistryField("indiv", COMMON, default_visible=True),
    RegistryField("species", COMMON, default_visible=True),
    RegistryField("sample_collection", COMMON, default_visible=True),
    RegistryField("sample_code", COMMON),
    RegistryField("catch_date", COMMON, default_visible=True),
    RegistryField("catch_year", COMMON, default_visible=True),
    RegistryField("result_type", COMMON),
    RegistryField("workbook", ANALYSIS, default_visible=True),
    RegistryField("rank", RESULTS, view=frozenset([PER_ASSIGNMENT]), default_visible=True),
    RegistryField("repunit", RESULTS, default_visible=True),
    RegistryField("probability", RESULTS, default_visible=True),
    RegistryField("top_collection", RESULTS, default_visible=True),
    RegistryField("CU", RESULTS),
    RegistryField("CU_NAME", RESULTS, default_visible=True),
    RegistryField("pbt_brood_year", RESULTS),
    RegistryField("pbt_brood_collection", RESULTS),
    RegistryField("sex_id", RESULTS, default_visible=True),
    RegistryField("fish_age", RESULTS, default_visible=True),
    RegistryField("failed_result", RESULTS),
)

FIELDS_BY_TERM = {f.term: f for f in INDIVIDUAL_FIELDS}
