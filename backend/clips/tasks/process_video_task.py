import os
import requests
from celery import shared_task
from django.core.cache import cache
from django.conf import settings

from ..models import Video, VideoClip

FUNCLIP_SERVICE_URL = os.getenv("FUNCLIP_SERVICE_URL", "http://127.0.0.1:5000")


@shared_task(bind=True, max_retries=2)
def process_video_task(self, video_id: int) -> dict:
    """Processa vídeo com FunClip + FFmpeg"""
    try:
        video = Video.objects.get(id=video_id)
        video.status = "processing"
        video.task_id = self.request.id
        video.save()

        video_path = video.file.path
        output_dir = os.path.join(settings.MEDIA_ROOT, f"clips/{video_id}")
        os.makedirs(output_dir, exist_ok=True)

        # Stage 1: FunClip - Reconhecimento
        cache.set(f"video_progress_{video_id}", 25, timeout=3600)
        srt_file = _run_funclip_stage1(video_path, output_dir)
        clips_info = _parse_srt_file(srt_file)

        # Stage 2: FunClip - Corte
        cache.set(f"video_progress_{video_id}", 50, timeout=3600)
        clips_data = _run_funclip_stage2(video_path, output_dir, clips_info, video_id)

        # Salvar no banco
        cache.set(f"video_progress_{video_id}", 75, timeout=3600)
        for clip_info in clips_data:
            VideoClip.objects.create(
                video=video,
                title=clip_info["title"],
                start_time=clip_info["start_time"],
                end_time=clip_info["end_time"],
            )

        video.status = "completed"
        video.save()
        cache.set(f"video_progress_{video_id}", 100, timeout=3600)

        return {"video_id": video_id, "status": "completed"}

    except Video.DoesNotExist:
        return {"error": "Video not found", "status": "failed"}
    except Exception as e:
        try:
            video = Video.objects.get(id=video_id)
            video.status = "failed"
            video.save()
        except:
            pass
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


def _run_funclip_stage1(video_path: str, output_dir: str) -> str:
    """Executa FunClip Stage 1: Reconhecimento de Fala via HTTP"""
    try:
        response = requests.post(
            f"{FUNCLIP_SERVICE_URL}/stage1",
            json={
                "video_path": video_path,
                "output_dir": output_dir,
            },
            timeout=610
        )
        
        if response.status_code != 200:
            error = response.json().get("error", "Unknown error")
            raise Exception(f"FunClip Stage 1 failed: {error}")
        
        data = response.json()
        if not data.get("success"):
            raise Exception(f"FunClip Stage 1 failed: {data.get('error')}")
        
        srt_file = data.get("srt_file")
        if not os.path.exists(srt_file):
            raise Exception(f"SRT file not generated: {srt_file}")
        
        return srt_file
    
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to FunClip service at {FUNCLIP_SERVICE_URL}")
    except requests.exceptions.Timeout:
        raise Exception("FunClip Stage 1 timeout")
    except Exception as e:
        raise Exception(f"FunClip Stage 1 failed: {str(e)}")


def _run_funclip_stage2(video_path: str, output_dir: str, clips_info: list, video_id: int) -> list:
    """Executa FunClip Stage 2: Corte de Vídeos via HTTP"""
    clips_data = []

    for idx, clip_info in enumerate(clips_info):
        start_time = clip_info["start"]
        end_time = clip_info["end"]
        title = clip_info.get("title", f"Clip {idx + 1}")
        output_file = os.path.join(output_dir, f"clip_{idx + 1}.mp4")

        try:
            response = requests.post(
                f"{FUNCLIP_SERVICE_URL}/stage2",
                json={
                    "video_path": video_path,
                    "output_dir": output_dir,
                    "dest_text": title,
                    "start_ost": int(start_time),
                    "end_ost": int(end_time),
                    "output_file": output_file,
                },
                timeout=310
            )
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            if data.get("success") and os.path.exists(output_file):
                clips_data.append({
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "file_path": output_file,
                })
        
        except (requests.exceptions.RequestException, Exception):
            continue

    if not clips_data:
        raise Exception("No clips generated")

    return clips_data


def _parse_srt_file(srt_file: str) -> list:
    """Parse SRT file e extrai timestamps"""
    if not os.path.exists(srt_file):
        raise Exception(f"SRT file not found: {srt_file}")

    clips = []
    with open(srt_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    clip_index = 1
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            times = line.split("-->")
            start_seconds = _srt_time_to_seconds(times[0].strip())
            end_seconds = _srt_time_to_seconds(times[1].strip())

            title = f"Clip {clip_index}"
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.isdigit():
                    title = next_line[:100]

            clips.append({"start": start_seconds, "end": end_seconds, "title": title})
            clip_index += 1

        i += 1

    return clips


def _srt_time_to_seconds(time_str: str) -> float:
    """Converte tempo SRT (HH:MM:SS,mmm) para segundos"""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
