from rest_framework import serializers

#  Output shape
# [
#   {
#     "term": "indiv",
#     "definition": "individual fish identifier, ...",
#     "frontend_term": "Individual ID",
#     "original_workbook_term": "indiv",
#     "group": "Individual",
#     "default_visible": true,
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
    default_visible = serializers.BooleanField()
    views = serializers.ListField(child=serializers.CharField())

