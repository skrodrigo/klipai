import logging
from ..models import Job

logger = logging.getLogger(__name__)


def get_plan_tier(plan: str | None) -> str:
    p = (plan or "").strip().lower()
    return "business" if p == "business" else "starter"


def update_job_status(
    video_id: str,
    status: str,
    progress: int = None,
    current_step: str = None
) -> bool:

    try:
        update_fields = {
            "status": status,
        }

        if progress is not None:
            update_fields["progress"] = progress
        
        if current_step is not None:
            update_fields["current_step"] = current_step

        affected = Job.objects.filter(video_id=video_id).update(**update_fields)
        
        if affected == 0:
            logger.warning(f"[job_utils] Job não encontrado para video_id={video_id}")
            return False
        
        logger.debug(
            f"[job_utils] Job atualizado: video_id={video_id}, "
            f"status={status}, progress={progress}"
        )
        return True

    except Exception as e:
        logger.error(
            f"[job_utils] Erro crítico ao atualizar job {video_id}: {e}",
            exc_info=True
        )
        return False
