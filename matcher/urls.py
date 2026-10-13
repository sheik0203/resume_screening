from django.urls import path

from . import views


app_name = "matcher"

urlpatterns = [
    path("", views.upload_resumes, name="upload"),
]
