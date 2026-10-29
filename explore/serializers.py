from rest_framework import serializers

#  Output shape
# [
#   {
#     "term": "indiv",
#     "label": "Individual ID",
#     "definition": "individual fish identifier, ...",
#     "workbook_terms": ["indiv"],
#     "group": "Individual",
#     "default_visible": true,
#     "views": ["per_assignment", "per_fish"]
#   },
#   ...
# ]


class IndividualFieldSerializer(serializers.Serializer):
    term = serializers.CharField()
    label = serializers.CharField(allow_null=True)
    definition = serializers.CharField(allow_null=True)
    workbook_terms = serializers.ListField(child=serializers.CharField())
    group = serializers.CharField()
    default_visible = serializers.BooleanField()
    views = serializers.ListField(child=serializers.CharField())

