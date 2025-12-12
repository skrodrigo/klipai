from typing import Any, Dict, List

from ..models import Video


def list_videos() -> List[Dict[str, Any]]:
    """
    Lista todos os vídeos ordenados por data de criação (mais recentes primeiro).
    
    Returns:
        Lista de dicts com id, title, created_at, status, progress
    """
    from django.core.cache import cache
    
    videos = []
    for video in Video.objects.order_by("-created_at"):
        status_data = cache.get(f"video_status_{video.id}")
        progress = status_data.get("progress", 0) if status_data else 0
        videos.append({
            "id": video.id,
            "title": video.title,
            "created_at": video.created_at.isoformat(),
            "status": video.status,
            "progress": progress,
            "clips": [],
        })
    return videos
