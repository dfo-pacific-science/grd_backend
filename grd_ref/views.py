from rest_framework import viewsets

from . import models, serializers


class _RefViewSet(viewsets.ModelViewSet):
    search_fields = ["value"]
    ordering_fields = ["id", "value"]


class AdiposeRefViewSet(_RefViewSet):
    queryset = models.AdiposeRef.objects.all()
    serializer_class = serializers.AdiposeRefSerializer


class EstimatesTypeRefViewSet(_RefViewSet):
    queryset = models.EstimatesTypeRef.objects.all()
    serializer_class = serializers.EstimatesTypeRefSerializer


class GearRefViewSet(_RefViewSet):
    queryset = models.GearRef.objects.all()
    serializer_class = serializers.GearRefSerializer


class IdTypeRefViewSet(_RefViewSet):
    queryset = models.IdTypeRef.objects.all()
    serializer_class = serializers.IdTypeRefSerializer


class SexRefViewSet(_RefViewSet):
    queryset = models.SexRef.objects.all()
    serializer_class = serializers.SexRefSerializer


class SpeciesRefViewSet(_RefViewSet):
    queryset = models.SpeciesRef.objects.all()
    serializer_class = serializers.SpeciesRefSerializer
