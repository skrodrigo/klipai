from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..services.list_video_clips_service import list_video_clips


@csrf_exempt
def video_clips_list(request: HttpRequest, video_id: int) -> JsonResponse:
    """
    GET: Lista todos os clips de um vídeo específico
    """
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    clips = list_video_clips(video_id)
    return JsonResponse({"results": clips}, status=200)
