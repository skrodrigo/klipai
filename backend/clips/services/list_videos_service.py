from typing import Any, Dict, List

from ..models import Video


def list_videos() -> List[Dict[str, Any]]:
    """
    Lista todos os vídeos ordenados por data de criação (mais recentes primeiro).
    
    Returns:
        Lista de dicts com id, title, created_at
    """
    return list(
        Video.objects.order_by("-created_at").values("id", "title", "created_at")
    )
