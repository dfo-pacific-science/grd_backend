from grd.models import Individual, Workbook, IndividualRepunitResult
from django.db.models import Subquery, OuterRef, F, Q, Value

def individuals_per_fish():
    repunit_results = IndividualRepunitResult.objects.filter(individual=OuterRef("pk")).order_by(F("probability").desc(nulls_last=True), "id")
    
    return Individual.objects.select_related("workbook", "pbt").annotate(
        top_repunit=Subquery(
            repunit_results.values("repunit")[:1]
        ),
        top_probability=Subquery(
            repunit_results.values("probability")[:1]
        )
    )
    
    