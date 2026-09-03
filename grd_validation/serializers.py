from __future__ import annotations

from rest_framework import serializers

from . import models


class FileVersionSerializer(serializers.ModelSerializer):
    sha256_checksum = serializers.SerializerMethodField()

    class Meta:
        model = models.FileVersion
        fields = "__all__"

    def get_sha256_checksum(self, obj) -> str | None:
        return obj.sha256_checksum.hex() if obj.sha256_checksum is not None else None


class SheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sheet
        fields = "__all__"


class MappedTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MappedTerm
        fields = "__all__"


class RawTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RawTerm
        fields = "__all__"
