from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("file-versions", views.FileVersionViewSet)
router.register("sheets", views.SheetViewSet)
router.register("mapped-terms", views.MappedTermViewSet)
router.register("raw-terms", views.RawTermViewSet)

urlpatterns = router.urls
