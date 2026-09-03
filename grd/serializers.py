"""Serializers for the `grd` schema.

All columns are writable except `projects.sha256`, surfaced as a read-only hex
string (a NOT NULL binary column owned by the ingestion pipeline).
"""

from __future__ import annotations

from rest_framework import serializers

from . import models


class ProjectSerializer(serializers.ModelSerializer):
    sha256 = serializers.SerializerMethodField()

    class Meta:
        model = models.Project
        fields = "__all__"

    def get_sha256(self, obj) -> str | None:
        return obj.sha256.hex() if obj.sha256 is not None else None


class CollectionsAndGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CollectionsAndGroups
        fields = "__all__"


class ProjectBaselineFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectBaselineFile
        fields = "__all__"


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Inventory
        fields = "__all__"


class EstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estimate
        fields = "__all__"


class IndividualCollectionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualCollectionResult
        fields = "__all__"


class IndividualRepunitResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualRepunitResult
        fields = "__all__"


class IndividualRegionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualRegionResult
        fields = "__all__"


class IndividualCustomResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualCustomResult
        fields = "__all__"


class IndividualPbtSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualPbt
        fields = "__all__"


class IndividualExtractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualExtraction
        fields = "__all__"


class IndividualPositiveSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualPositiveSpecies
        fields = "__all__"


class IndividualNegativeSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualNegativeSpecies
        fields = "__all__"


class IndividualDuplicateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualDuplicate
        fields = "__all__"


class IndividualInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualInventory
        fields = "__all__"


class IndividualListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Individual
        fields = "__all__"


class IndividualDetailSerializer(IndividualListSerializer):
    """Individual with its assignment results and PBT nested inline (read-only)."""

    collection_results = IndividualCollectionResultSerializer(many=True, read_only=True)
    repunit_results = IndividualRepunitResultSerializer(many=True, read_only=True)
    region_results = IndividualRegionResultSerializer(many=True, read_only=True)
    custom_results = IndividualCustomResultSerializer(many=True, read_only=True)
    positive_species = IndividualPositiveSpeciesSerializer(many=True, read_only=True)
    negative_species = IndividualNegativeSpeciesSerializer(many=True, read_only=True)
    pbt = IndividualPbtSerializer(read_only=True)


class IndividualRunDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualRunData
        fields = "__all__"


class InventoryRunDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InventoryRunData
        fields = "__all__"
