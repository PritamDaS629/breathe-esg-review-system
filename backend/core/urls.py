from django.urls import path

from . import views

urlpatterns = [
    path("bootstrap/", views.bootstrap),
    path("activities/", views.activities),
    path("batches/", views.batches),
    path("upload/<str:source_type>/", views.upload_source),
    path("activities/<int:pk>/approve/", views.approve_activity),
    path("activities/<int:pk>/reject/", views.reject_activity),
]
