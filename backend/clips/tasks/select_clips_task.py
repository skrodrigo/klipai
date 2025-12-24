import logging
from celery import shared_task
import os

from ..models import Video, Transcript, Organization
from .job_utils import get_plan_tier, update_job_status

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def select_clips_task(self, video_id: str) -> dict:
    try:
        logger.info(f"Iniciando seleção de clips para video_id: {video_id}")
        
        video = Video.objects.get(video_id=video_id)
        org = Organization.objects.get(organization_id=video.organization_id)
        
        video.status = "selecting"
        video.current_step = "selecting"
        video.save()

        transcript = Transcript.objects.filter(video=video).first()
        if not transcript:
            raise Exception("Transcrição não encontrada")

        analysis_data = transcript.analysis_data or {}
        candidates = analysis_data.get("candidates", [])

        if not candidates:
            raise Exception("Nenhum candidato de clip encontrado na análise")

        min_duration, max_duration = _get_duration_bounds(video_id=video_id)
        target_clips = _estimate_target_clips(video_duration=video.duration, max_duration=max_duration)

        config = {
            "max_duration": max_duration,
            "min_duration": min_duration,
            "target_clips": target_clips,
            "min_score": 30,
        }

        selected_clips = _process_selection(candidates, config)

        min_target = int(os.getenv("MIN_TARGET_CLIPS", "10") or 10)

        if not selected_clips:
            logger.warning("Nenhum clip passou nos critérios. Relaxando regras...")
            # Relaxamento progressivo: score -> duração -> fallback por rank/tempo
            config["min_score"] = 10
            selected_clips = _process_selection(candidates, config)

        if not selected_clips:
            logger.warning("Ainda nenhum clip. Relaxando duração...")
            config["min_duration"] = 5
            config["max_duration"] = max(config["max_duration"], 90)
            selected_clips = _process_selection(candidates, config)

        if not selected_clips:
            logger.warning("Ainda nenhum clip. Usando fallback por rank (ignorando score mínimo).")
            selected_clips = _fallback_select_any(candidates, config)

        if selected_clips and len(selected_clips) < min_target:
            logger.warning(
                f"Selecionou apenas {len(selected_clips)} clips (min_target={min_target}). Tentando preencher..."
            )

            fill_cfg = dict(config)
            fill_cfg["target_clips"] = max(min_target, int(fill_cfg.get("target_clips") or min_target))

            fill_cfg["overlap_threshold"] = 0.92
            fill_cfg["min_score"] = min(fill_cfg.get("min_score", 10), 10)
            filled = _process_selection(candidates, fill_cfg)
            if len(filled) > len(selected_clips):
                selected_clips = filled

            if len(selected_clips) < min_target:
                fill_cfg["min_score"] = -1
                fill_cfg["fallback_min_gap"] = 0.5
                filled = _fallback_select_any(candidates, fill_cfg)
                if len(filled) > len(selected_clips):
                    selected_clips = filled

        if not selected_clips:
            raise Exception("Não foi possível selecionar nenhum clip válido")

        transcript.selected_clips = selected_clips
        transcript.save()

        video.last_successful_step = "selecting"
        video.status = "reframing"
        video.current_step = "reframing"
        video.save()
        
        update_job_status(str(video.video_id), "reframing", progress=70, current_step="reframing")

        from .reframe_video_task import reframe_video_task
        reframe_video_task.apply_async(
            args=[str(video.video_id)],
            queue=f"video.reframe.{get_plan_tier(org.plan)}",
        )

        return {
            "video_id": str(video.video_id),
            "selected_count": len(selected_clips),
            "top_score": selected_clips[0]["score"] if selected_clips else 0
        }

    except Video.DoesNotExist:
        return {"error": "Video not found", "status": "failed"}
    except Exception as e:
        logger.error(f"Erro na seleção {video_id}: {e}", exc_info=True)
        if video:
            video.status = "failed"
            video.error_message = str(e)
            video.save()

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)

        return {"error": str(e), "status": "failed"}


def _process_selection(candidates: list, config: dict) -> list:
    valid_candidates = []

    for c in candidates:
        start = float(c.get("start_time", 0))
        end = float(c.get("end_time", 0))
        duration = end - start
        
        if c.get("adjusted_engagement_score") is not None:
            score = float(c.get("adjusted_engagement_score", 0))
        else:
            engagement_score = float(c.get("engagement_score", 0))
            score = engagement_score * 10 

        score = round(score, 2)
        
        logger.debug(f"Candidato: start={start}, end={end}, duration={duration}s, score={score}/100")
        
        if duration < config["min_duration"] or duration > config["max_duration"]:
            logger.debug(f"  ❌ Duração fora do intervalo ({config['min_duration']}-{config['max_duration']}s)")
            continue
            
        if score < config["min_score"]:
            logger.debug(f"  ❌ Score baixo (min: {config['min_score']}/100)")
            continue

        logger.debug(f"  ✅ Candidato válido")
        valid_candidates.append({
            "start_time": start,
            "end_time": end,
            "duration": duration,
            "text": c.get("text", ""),
            "title": c.get("hook_title", "Viral Clip"),
            "score": score, 
            "reasoning": c.get("reasoning", "")
        })

    valid_candidates.sort(key=lambda x: x["score"], reverse=True)

    final_selection = []
    
    for candidate in valid_candidates:
        if len(final_selection) >= config["target_clips"]:
            break
            
        is_overlapping = False
        for selected in final_selection:
            if _check_overlap(candidate, selected):
                is_overlapping = True
                break
        
        if not is_overlapping:
            final_selection.append(candidate)
            
    return final_selection


def _fallback_select_any(candidates: list, config: dict) -> list:
    """Último recurso: sempre retornar algo razoável.

    Estratégia:
    - Converte candidatos em formato interno.
    - Ordena por score.
    - Seleciona respeitando uma distância mínima entre clips.
    - Se precisar, ajusta (clamp) a duração para ficar dentro de min/max.
    """
    try:
        items = []
        for c in candidates:
            start = float(c.get("start_time", 0) or 0)
            end = float(c.get("end_time", 0) or 0)
            if end <= start:
                continue

            if c.get("adjusted_engagement_score") is not None:
                score = float(c.get("adjusted_engagement_score", 0) or 0)
            else:
                score = float(c.get("engagement_score", 0) or 0) * 10

            items.append(
                {
                    "start_time": start,
                    "end_time": end,
                    "duration": end - start,
                    "text": c.get("text", ""),
                    "title": c.get("hook_title", "Viral Clip"),
                    "score": round(float(score), 2),
                    "reasoning": c.get("reasoning", ""),
                }
            )

        if not items:
            return []

        items.sort(key=lambda x: x["score"], reverse=True)

        min_d = float(config.get("min_duration") or 5)
        max_d = float(config.get("max_duration") or 90)
        target = int(config.get("target_clips") or 6)

        # distância mínima (em segundos) entre clips no fallback
        min_gap = float(config.get("fallback_min_gap", 3.0) or 3.0)

        selected = []
        for it in items:
            if len(selected) >= target:
                break

            # Ajusta duração para não descartar tudo
            start = float(it["start_time"])
            end = float(it["end_time"])
            dur = end - start

            if dur < min_d:
                end = start + min_d
            elif dur > max_d:
                end = start + max_d

            candidate = {
                **it,
                "end_time": end,
                "duration": end - start,
            }

            # garante espaçamento mínimo
            if any(abs(candidate["start_time"] - s["start_time"]) < min_gap for s in selected):
                continue

            selected.append(candidate)

        # Se ainda vazio, pega o melhor mesmo sem gap
        if not selected:
            best = items[0]
            start = float(best["start_time"])
            end = float(best["end_time"])
            dur = end - start
            if dur < min_d:
                end = start + min_d
            elif dur > max_d:
                end = start + max_d
            return [{**best, "end_time": end, "duration": end - start}]

        return selected
    except Exception:
        return []


def _check_overlap(clip_a: dict, clip_b: dict, threshold: float = 0.75) -> bool:
    start_a, end_a = clip_a["start_time"], clip_a["end_time"]
    start_b, end_b = clip_b["start_time"], clip_b["end_time"]

    intersection_start = max(start_a, start_b)
    intersection_end = min(end_a, end_b)
    
    if intersection_end < intersection_start:
        return False
    intersection_duration = intersection_end - intersection_start

    if intersection_duration > threshold:
        return True

    return False


def _get_duration_bounds(video_id: str) -> tuple[int, int]:
    """Busca min/max duration a partir de Job.configuration quando existir.

    Compatível com:
    - job.configuration.max_clip_duration
    - job.configuration.maxDuration
    - defaults
    """
    try:
        from ..models import Job
        job = Job.objects.filter(video_id=video_id).order_by("-created_at").first()
        cfg = (job.configuration if job else None) or {}

        max_d = cfg.get("max_clip_duration") or cfg.get("maxDuration")
        if max_d is None:
            max_d = 60

        max_d = int(max(10, min(int(max_d), 180)))

        min_d = cfg.get("min_clip_duration") or cfg.get("minDuration")
        if min_d is None:
            min_d = max(10, int(round(max_d * 0.6)))

        min_d = int(max(5, min(int(min_d), max_d)))
        return min_d, max_d
    except Exception:
        return 10, 60


def _estimate_target_clips(video_duration: float | None, max_duration: int) -> int:
    try:
        if not video_duration or video_duration <= 0:
            return 6

        min_target = int(os.getenv("MIN_TARGET_CLIPS", "10") or 10)
        max_target = int(os.getenv("MAX_TARGET_CLIPS", "40") or 40)

        est = int(video_duration // max(15.0, (max_duration * 1.8)))
        est = max(min_target, est)
        return min(est, max_target)
    except Exception:
        return 6
