import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache

@csrf_exempt
@require_POST
def video_status_update_view(request, video_id: int):
    """
    Webhook para receber atualizações de status da tarefa Celery e publicar no Redis.
    """
    try:
        data = json.loads(request.body)
        status = data.get("status")
        progress = data.get("progress")

        if not status:
            return JsonResponse({"error": "Status is required"}, status=400)

        # Salva o status no cache
        cache.set(f'video_status_{video_id}', data, timeout=3600)
        
        return JsonResponse({"message": "Update received"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
