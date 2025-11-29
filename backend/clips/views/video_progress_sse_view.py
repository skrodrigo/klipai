from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache


@csrf_exempt
def video_progress_sse(request, video_id: int):
    """
    Server-Sent Events endpoint para monitorar progresso de processamento.
    Frontend se conecta e recebe atualizações em tempo real.
    """
    def event_stream():
        last_progress = -1
        max_attempts = 300  # 5 minutos com polling de 1s

        for _ in range(max_attempts):
            progress = cache.get(f"video_progress_{video_id}", -1)

            if progress != last_progress:
                last_progress = progress
                if progress == 100:
                    yield f"data: {{'progress': 100, 'status': 'completed'}}\n\n"
                    break
                elif progress >= 0:
                    yield f"data: {{'progress': {progress}, 'status': 'processing'}}\n\n"

            # Aguarda 1 segundo antes de próxima verificação
            import time
            time.sleep(1)

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
