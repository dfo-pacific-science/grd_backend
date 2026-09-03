from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register("projects", views.ProjectViewSet)
router.register("collections-and-groups", views.CollectionsAndGroupsViewSet)
router.register("baseline-files", views.ProjectBaselineFileViewSet)
router.register("inventories", views.InventoryViewSet)
router.register("estimates", views.EstimateViewSet)
router.register("individuals", views.IndividualViewSet)
router.register("collection-results", views.IndividualCollectionResultViewSet)
router.register("repunit-results", views.IndividualRepunitResultViewSet)
router.register("region-results", views.IndividualRegionResultViewSet)
router.register("custom-results", views.IndividualCustomResultViewSet)
router.register("pbt", views.IndividualPbtViewSet)
router.register("extractions", views.IndividualExtractionViewSet)
router.register("positive-species", views.IndividualPositiveSpeciesViewSet)
router.register("negative-species", views.IndividualNegativeSpeciesViewSet)
router.register("duplicates", views.IndividualDuplicateViewSet)
router.register("individual-inventories", views.IndividualInventoryViewSet)
router.register("run-data/individuals", views.IndividualRunDataViewSet)
router.register("run-data/inventories", views.InventoryRunDataViewSet)

urlpatterns = router.urls
