# Temporary dictionary values for the individuals fields, used until the data dictionary is
# loaded into grd_validation.mapped_terms (3.1). Holds only what the dictionary will provide:
# label, definition and workbook terms. Group, order, defaults and views come from registry.py.
# Delete this file once mapped_terms has labels for every registry term.

DICTIONARY_STUB = {
    "indiv": {
        "label": "Individual ID",
        "definition": "Individual fish identifier.",
    },
    "sample_collection": {
        "label": "Sample collection",
        "definition": "A unique identifier associated with samples collected and analysed together within the same project, formatted as Source_AreaCode(Year)_Month(MonthName). Multiple sample_collections can exist under each SampleCode.",
    },
    "sample_code": {
        "label": "Sample code",
        "definition": "A numeric code (increasing from 1) assigned to mixture samples, typically representing batches of samples submitted and requested for analysis together. It forms the first part of the \"indiv\" identifier, and is the same as \"StockCode\" in \"extraction_sheet\".",
    },
    "catch_date": {
        "label": "Catch date",
        "definition": "Date the fish was caught (YYYY-MM-DD).",
    },
    "catch_year": {
        "label": "Catch year",
        "definition": "Catch year.",
    },
    "result_type": {
        "label": "Result type",
        "definition": "How the fish was assigned to stock: GSI (Genetic Stock Identification) or PBT (Parentage Based Tagging).",
    },
    "rank": {
        "label": "Rank",
        "definition": "Rank of this repunit assignment for the fish, ordered by probability (1 = top assignment).",
    },
    "repunit": {
        "label": "Repunit",
        "definition": "The genetic reporting scale at which the analysis was considered, typically combining rivers or CUs with indistinguishable or poorly distinguished genetic profiles. Repunits often follow Conservation Unit delineation in Canada, and regional groupings in the US, but may be adjusted (as defined on the baseline_collections tab) based on the specific question at-hand and the available mixture sample size.",
    },
    "probability": {
        "label": "Probability",
        "definition": "Statistical confidence value representing the likelihood that the assigned genetic classification (e.g., parentage or reporting unit) is correct.",
    },
    "top_collection": {
        "label": "Top collection",
        "definition": "The baseline collection (population) with the highest assignment probability for the fish, when provided by the lab.",
    },
    "top_collection_probability": {
        "label": "Top collection probability",
        "definition": "The probability associated with the top baseline collection (population) for the fish.",
    },
    "pbt_brood_year": {
        "label": "PBT brood year",
        "definition": "Brood Year of parents to which individual was assigned via PBT.",
    },
    "pbt_brood_collection": {
        "label": "PBT brood collection",
        "definition": "The river system, waterbody or location where broodstock individuals are collected for Parentage-Based Tagging (PBT) analysis.",
    },
    "sex_id": {
        "label": "Sex",
        "definition": "male / presumed_female / unknown",
    },
    "fish_age": {
        "label": "Age",
        "definition": "Estimated age of the fish in mixture based on assignment to parents of brood years.",
    },
    "failed_result": {
        "label": "Failed result",
        "definition": "Reason no stock result was reported: Too few loci, Failed to amplify, Non-target species or Likely duplicate.",
    },
}
