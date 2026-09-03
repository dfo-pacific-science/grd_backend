"""ViewSets for the `grd` schema.

Full CRUD on every real table. The two `*_run_data_v` database views are
read-only (Postgres won't accept writes through them).

Caveats for these ``managed = False`` tables:
- `projects` has a NOT NULL `sha256` binary column serialized as read-only hex —
  create project rows via the ingestion pipeline, not the API; update works.
- deletes are blocked by the database while foreign-key children still exist.
"""

from rest_framework import viewsets

from . import filters, models, serializers


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filterset_class = filters.ProjectFilter
    search_fields = ["original_filename", "pipeline_version", "baseline_file"]
    ordering_fields = ["id", "ingestion_date", "date_run", "species_id"]


class CollectionsAndGroupsViewSet(viewsets.ModelViewSet):
    queryset = models.CollectionsAndGroups.objects.all()
    serializer_class = serializers.CollectionsAndGroupsSerializer
    filterset_fields = ["project", "group", "collection"]
    search_fields = ["group", "collection"]
    ordering_fields = ["id", "group_display_order", "collection_display_order"]


class ProjectBaselineFileViewSet(viewsets.ModelViewSet):
    queryset = models.ProjectBaselineFile.objects.all()
    serializer_class = serializers.ProjectBaselineFileSerializer
    filterset_fields = ["project", "repunit", "collection", "cu"]
    search_fields = ["repunit", "collection", "cu", "cu_name"]
    ordering_fields = ["id", "display_order"]


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = models.Inventory.objects.all()
    serializer_class = serializers.InventorySerializer
    filterset_class = filters.InventoryFilter
    search_fields = ["sample_collection", "sample_code", "contact", "area_fished"]
    ordering_fields = ["id", "sample_collection"]


class EstimateViewSet(viewsets.ModelViewSet):
    queryset = models.Estimate.objects.all()
    serializer_class = serializers.EstimateSerializer
    filterset_class = filters.EstimateFilter
    search_fields = ["conservation_unit_code", "conservation_unit_name", "repunit", "region"]
    ordering_fields = ["id", "point_estimate", "estimates_type"]


class IndividualViewSet(viewsets.ModelViewSet):
    queryset = models.Individual.objects.select_related("project").all()
    filterset_class = filters.IndividualFilter
    search_fields = ["indiv", "mgl_pid", "mgl_pid_batch", "top_collection", "stamp_id"]
    ordering_fields = ["id", "catch_date", "catch_year", "top_collection_probability"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.IndividualDetailSerializer
        return serializers.IndividualListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "collection_results", "repunit_results", "region_results",
                "custom_results", "positive_species", "negative_species", "pbt",
            )
        return qs


class IndividualCollectionResultViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualCollectionResult.objects.all()
    serializer_class = serializers.IndividualCollectionResultSerializer
    filterset_class = filters.CollectionResultFilter
    ordering_fields = ["id", "probability", "collection"]


class IndividualRepunitResultViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualRepunitResult.objects.all()
    serializer_class = serializers.IndividualRepunitResultSerializer
    filterset_class = filters.RepunitResultFilter
    ordering_fields = ["id", "probability", "repunit"]


class IndividualRegionResultViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualRegionResult.objects.all()
    serializer_class = serializers.IndividualRegionResultSerializer
    filterset_class = filters.RegionResultFilter
    ordering_fields = ["id", "probability", "region"]


class IndividualCustomResultViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualCustomResult.objects.all()
    serializer_class = serializers.IndividualCustomResultSerializer
    filterset_class = filters.CustomResultFilter
    ordering_fields = ["id", "probability", "group"]


class IndividualPbtViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualPbt.objects.all()
    serializer_class = serializers.IndividualPbtSerializer
    filterset_fields = ["individual", "pbt_brood_year", "pbt_brood_collection", "pbt_brood_group"]


class IndividualExtractionViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualExtraction.objects.all()
    serializer_class = serializers.IndividualExtractionSerializer
    filterset_fields = ["individual"]


class IndividualPositiveSpeciesViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualPositiveSpecies.objects.all()
    serializer_class = serializers.IndividualPositiveSpeciesSerializer
    filterset_fields = ["individual", "positive_species_id", "pos_sp_id"]


class IndividualNegativeSpeciesViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualNegativeSpecies.objects.all()
    serializer_class = serializers.IndividualNegativeSpeciesSerializer
    filterset_fields = ["individual", "negative_species_confirmed"]


class IndividualDuplicateViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualDuplicate.objects.all()
    serializer_class = serializers.IndividualDuplicateSerializer
    filterset_fields = ["individual_1", "individual_2"]
    ordering_fields = ["id", "num_match", "num_non_miss"]


class IndividualInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.IndividualInventory.objects.all()
    serializer_class = serializers.IndividualInventorySerializer
    filterset_fields = ["individual", "inventory"]


class IndividualRunDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.IndividualRunData.objects.all()
    serializer_class = serializers.IndividualRunDataSerializer
    filterset_fields = ["species_id", "species", "date_run"]
    search_fields = ["indiv", "species"]
    ordering_fields = ["id", "date_run", "species"]


class InventoryRunDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.InventoryRunData.objects.all()
    serializer_class = serializers.InventoryRunDataSerializer
    filterset_fields = ["species_id", "species", "date_run"]
    search_fields = ["sample_collection", "species"]
    ordering_fields = ["id", "date_run", "species"]
