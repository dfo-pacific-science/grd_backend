import django_filters as df
from rest_framework import viewsets

from . import models, serializers


class FileVersionFilter(df.FilterSet):
    class Meta:
        model = models.FileVersion
        fields = {
            "format_name": ["exact", "icontains"],
            "original_filename": ["exact", "icontains"],
            "sheet_data_loaded": ["exact"],
            "grd_data_loaded": ["exact"],
            "date_added": ["exact", "gte", "lte"],
        }


class FileVersionViewSet(viewsets.ModelViewSet):
    queryset = models.FileVersion.objects.all()
    serializer_class = serializers.FileVersionSerializer
    filterset_class = FileVersionFilter
    search_fields = ["format_name", "original_filename", "comment"]
    ordering_fields = ["id", "date_added"]


class SheetViewSet(viewsets.ModelViewSet):
    queryset = models.Sheet.objects.select_related("file").all()
    serializer_class = serializers.SheetSerializer
    filterset_fields = ["file", "sheet_name"]
    search_fields = ["sheet_name"]
    ordering_fields = ["id", "sheet_name"]


class MappedTermViewSet(viewsets.ModelViewSet):
    queryset = models.MappedTerm.objects.all()
    serializer_class = serializers.MappedTermSerializer
    search_fields = ["term", "definition"]
    ordering_fields = ["id", "term"]


class RawTermViewSet(viewsets.ModelViewSet):
    queryset = models.RawTerm.objects.select_related("mapped_term").all()
    serializer_class = serializers.RawTermSerializer
    filterset_fields = ["mapped_term"]
    search_fields = ["term", "definition"]
    ordering_fields = ["id", "term"]
