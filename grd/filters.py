import django_filters as filters

from . import models


class ProjectFilter(filters.FilterSet):
    ingestion_date_after = filters.DateFilter(field_name="ingestion_date", lookup_expr="gte")
    ingestion_date_before = filters.DateFilter(field_name="ingestion_date", lookup_expr="lte")

    class Meta:
        model = models.Project
        fields = {
            "species_id": ["exact"],
            "pipeline_version": ["exact"],
            "original_filename": ["exact", "icontains"],
            "date_run": ["exact", "gte", "lte"],
        }


class IndividualFilter(filters.FilterSet):
    class Meta:
        model = models.Individual
        fields = {
            "project": ["exact"],
            "indiv": ["exact", "icontains"],
            "id_source": ["exact"],
            "top_collection": ["exact", "icontains"],
            "top_collection_probability": ["gte", "lte"],
            "catch_year": ["exact", "gte", "lte"],
            "catch_date": ["exact", "gte", "lte"],
            "sex_id": ["exact"],
            "mgl_pid": ["exact"],
            "mgl_pid_batch": ["exact"],
        }


class InventoryFilter(filters.FilterSet):
    class Meta:
        model = models.Inventory
        fields = {
            "project": ["exact"],
            "sample_collection": ["exact", "icontains"],
            "sample_code": ["exact"],
            "contact": ["exact", "icontains"],
        }


class EstimateFilter(filters.FilterSet):
    class Meta:
        model = models.Estimate
        fields = {
            "inventory": ["exact"],
            "estimates_type": ["exact"],
            "conservation_unit_code": ["exact"],
            "repunit": ["exact"],
            "region": ["exact"],
            "group": ["exact"],
            "point_estimate": ["gte", "lte"],
        }


class _ResultFilter(filters.FilterSet):
    probability_min = filters.NumberFilter(field_name="probability", lookup_expr="gte")
    probability_max = filters.NumberFilter(field_name="probability", lookup_expr="lte")


class CollectionResultFilter(_ResultFilter):
    class Meta:
        model = models.IndividualCollectionResult
        fields = {"individual": ["exact"], "collection": ["exact", "icontains"]}


class RepunitResultFilter(_ResultFilter):
    class Meta:
        model = models.IndividualRepunitResult
        fields = {"individual": ["exact"], "repunit": ["exact", "icontains"]}


class RegionResultFilter(_ResultFilter):
    class Meta:
        model = models.IndividualRegionResult
        fields = {"individual": ["exact"], "region": ["exact", "icontains"]}


class CustomResultFilter(_ResultFilter):
    class Meta:
        model = models.IndividualCustomResult
        fields = {"individual": ["exact"], "group": ["exact", "icontains"]}
