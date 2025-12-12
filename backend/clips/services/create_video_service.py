from typing import Any, Dict

from ..models import Video
import requests

from ..tasks.process_video_task import process_video_task


def create_video_with_clips(title: str, file) -> Dict[str, Any]:
    """
    Cria um vídeo e dispara task Celery para processar.
    
    Args:
        title: Título do vídeo
        file: Arquivo de vídeo
        
    Returns:
        Dict com dados do vídeo e task_id
    """
    video = Video.objects.create(title=title, file=file, status="pending")

    # Envia o estado inicial via webhook para notificar o SSE
    api_url = f"http://localhost:8000/api/videos/{video.id}/status/"
    requests.post(api_url, json={
        "status": "queue",
        "progress": 0,
        "queue_position": 1
    })

    # Dispara task Celery
    task = process_video_task.delay(video.id)
    video.task_id = task.id
    video.save()
    
    return {
        "id": video.id,
        "title": video.title,
        "status": video.status,
        "task_id": task.id,
        "created_at": video.created_at.isoformat(),
    }
