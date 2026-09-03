from rest_framework import serializers

from . import models


def _ref_serializer(ref_model):
    return type(
        f"{ref_model.__name__}Serializer",
        (serializers.ModelSerializer,),
        {"Meta": type("Meta", (), {"model": ref_model, "fields": ("id", "value")})},
    )


AdiposeRefSerializer = _ref_serializer(models.AdiposeRef)
EstimatesTypeRefSerializer = _ref_serializer(models.EstimatesTypeRef)
GearRefSerializer = _ref_serializer(models.GearRef)
IdTypeRefSerializer = _ref_serializer(models.IdTypeRef)
SexRefSerializer = _ref_serializer(models.SexRef)
SpeciesRefSerializer = _ref_serializer(models.SpeciesRef)
