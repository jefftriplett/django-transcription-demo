from django.urls import path

from . import views

app_name = "transcripts"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("<str:youtube_id>/", views.transcript_detail, name="detail"),
]
