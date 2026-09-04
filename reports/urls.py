from django.urls import path

from . import views

# Paths mirror the Next.js routes (app/api/*) so the frontend swap is a base-URL change.
urlpatterns = [
    path("individuals", views.individuals),
    path("individuals/download", views.individuals_download),
    path("bsciDNAResults", views.bsci_dna_results),
    path("bsciDNAResults/download", views.bsci_dna_results_download),
    path("scBDWRDNA", views.sc_bdwr_dna),
    path("scBDWRDNA/download", views.sc_bdwr_dna_download),
    path("estimateCatchByStockAge", views.estimate_catch_by_stock_age),
    path("estimateCatchByStockAge/download", views.estimate_catch_by_stock_age_download),
    path("projects", views.projects),
    path("projects/download", views.projects_download),
    path("sampleCollections", views.sample_collections),
    path("sampleCollections/download", views.sample_collections_download),
    path("stockProportionEstimates", views.stock_proportion_estimates),
    path("stockProportionEstimates/download", views.stock_proportion_estimates_download),
    path("dataLoad", views.data_load),
    path("dataLoad/download", views.data_load_download),
    # filter-option lookups
    path("options/species", views.options_species),
    path("options/idSources", views.options_id_sources),
    path("options/years", views.options_years),
    path("options/sampleCodes", views.options_sample_codes),
]
