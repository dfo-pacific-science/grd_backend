from rest_framework import serializers

#  Output shape
# [
#   {
#     "term": "indiv",
#     "definition": "individual fish identifier, ...",
#     "label": "Individual ID",
#     "original_workbook_term": "indiv",
#     "group": "Common",
#     "default_for": ["GSI", "PBT"],
#     "views": ["per_assignment", "per_fish"]
#   },
#   ...
# ]


class IndividualFieldSerializer(serializers.Serializer):
    term = serializers.CharField()
    definition = serializers.CharField(allow_null=True)
    label = serializers.CharField(allow_null=True)
    original_workbook_term = serializers.CharField(allow_null=True)
    group = serializers.CharField()
    # id_source groups (GSI, PBT, FAILED) this field is a default column for (4.15); empty means selectable only.
    default_for = serializers.ListField(child=serializers.CharField())
    views = serializers.ListField(child=serializers.CharField())

