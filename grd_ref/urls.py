from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("adipose", views.AdiposeRefViewSet)
router.register("estimates-type", views.EstimatesTypeRefViewSet)
router.register("gear", views.GearRefViewSet)
router.register("id-type", views.IdTypeRefViewSet)
router.register("sex", views.SexRefViewSet)
router.register("species", views.SpeciesRefViewSet)

urlpatterns = router.urls
