from django.urls import path

from .views.videos_list_create_view import videos_list_create
from .views.video_clips_list_view import video_clips_list
from .views.video_progress_sse_view import video_progress_sse


urlpatterns = [
    path("videos/", videos_list_create, name="videos-list-create"),
    path("videos/<int:video_id>/clips/", video_clips_list, name="video-clips-list"),
    path("videos/<int:video_id>/progress/", video_progress_sse, name="video-progress-sse"),
]
