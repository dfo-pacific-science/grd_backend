from django.urls import path

# from . import views

urlpatterns = [
    # Filled in as views are added
    path("individuals/fields/", views.IndividualFieldsView.as_view(), name="individual-fields"),
]

