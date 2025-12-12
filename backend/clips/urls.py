from django.urls import path, re_path, re_path

from .views.videos_list_create_view import videos_list_create
from .views.video_clips_list_view import video_clips_list
from .views.video_progress_sse_view import video_progress_sse
from .views.video_status_update_view import video_status_update_view


urlpatterns = [
    path("videos/", videos_list_create, name="videos-list-create"),
    path("videos/<int:video_id>/clips/", video_clips_list, name="video-clips-list"),
    re_path(r"^videos/(?P<video_id>\d+)/progress/?$", video_progress_sse, name="video-progress-sse"),
    path("videos/<int:video_id>/status/", video_status_update_view, name="video-status-update"),
]
