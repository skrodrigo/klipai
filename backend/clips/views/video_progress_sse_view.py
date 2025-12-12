import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from clips.models.video import Video


@csrf_exempt
def video_progress_sse(request, video_id: int):
    video = get_object_or_404(Video, pk=video_id)
    """
    Server-Sent Events endpoint para monitorar progresso de processamento.
    Frontend se conecta e recebe atualizações em tempo real.
    """
    def event_stream():
        last_status = None
        max_attempts = 1800  # Limite para evitar loops infinitos (30 minutos)

        for _ in range(max_attempts):
            status_data = cache.get(f"video_status_{video_id}")
            
            if status_data is None:
                # Se não houver dados no cache, envia um status de "fila"
                status_data = {
                    "status": "queue",
                    "progress": 0,
                    "queue_position": None
                }

            if status_data != last_status:
                last_status = status_data
                yield f"data: {json.dumps(status_data)}\n\n"
                
                if status_data.get("status") in ["completed", "failed"]:
                    break

            import time
            time.sleep(1)

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
