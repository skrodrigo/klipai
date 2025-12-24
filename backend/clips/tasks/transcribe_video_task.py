import logging
import os
import json
import subprocess
from celery import shared_task
from django.conf import settings
import google.generativeai as genai

from ..models import Video, Transcript, Organization
from .job_utils import get_plan_tier, update_job_status
from ..services.storage_service import R2StorageService

logger = logging.getLogger(__name__)

_gemini_configured = False


@shared_task(bind=True, max_retries=3)
def transcribe_video_task(self, video_id: str) -> dict:
    audio_path = None
    try:
        logger.info(f"Iniciando transcrição para video_id: {video_id}")
        
        video = Video.objects.get(video_id=video_id)
        org = Organization.objects.get(organization_id=video.organization_id)
        
        video.status = "transcribing"
        video.current_step = "transcribing"
        video.save()
        update_job_status(str(video.video_id), "transcribing", progress=35, current_step="transcribing")

        video_dir = os.path.join(settings.MEDIA_ROOT, f"videos/{video_id}")
        
        video_path = os.path.join(video_dir, "video_normalized.mp4")
        if not os.path.exists(video_path):
            raise Exception("Arquivo video_normalized.mp4 não encontrado")

        audio_path = _extract_audio_with_ffmpeg(video_path, video_dir)

        transcript_data = _transcribe_with_whisper(audio_path)

        # Opcional: pós-processamento com Gemini para corrigir gírias/jargões/metáforas.
        # Mantém timestamps (start/end) e word-timestamps; altera apenas os textos.
        if bool(getattr(settings, "GEMINI_REFINE_WHISPER_TRANSCRIPT", False)):
            try:
                transcript_data = _refine_transcript_with_gemini(transcript_data)
            except Exception as e:
                logger.warning(f"[transcribe] Gemini refine falhou; seguindo com Whisper original: {e}")

        json_path = os.path.join(video_dir, "transcript.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        srt_path = os.path.join(video_dir, "transcript.srt")
        _save_srt_file(transcript_data, srt_path)

        storage = R2StorageService()
        transcript_storage_path = storage.upload_transcript(
            file_path=json_path,
            organization_id=str(video.organization_id),
            video_id=str(video.video_id),
        )

        Transcript.objects.update_or_create(
            video=video,
            defaults={
                "full_text": transcript_data.get("full_text", ""),
                "segments": transcript_data.get("segments", []),
                "language": transcript_data.get("language", "en"),
                "confidence_score": transcript_data.get("confidence_score", 0),
                "storage_path": transcript_storage_path,
            }
        )

        if os.path.exists(audio_path):
            os.remove(audio_path)

        video.last_successful_step = "transcribing"
        video.status = "analyzing"
        video.current_step = "analyzing"
        video.save()
        
        update_job_status(str(video.video_id), "analyzing", progress=40, current_step="analyzing")

        from .analyze_semantic_task import analyze_semantic_task
        analyze_semantic_task.apply_async(
            args=[str(video.video_id)],
            queue=f"video.analyze.{get_plan_tier(org.plan)}",
        )

        return {
            "video_id": str(video.video_id),
            "language": transcript_data.get("language"),
            "words_count": len(transcript_data.get("full_text", "").split()),
        }

    except Video.DoesNotExist:
        return {"error": "Video not found", "status": "failed"}
    except Exception as e:
        logger.error(f"Erro transcrição {video_id}: {str(e)}", exc_info=True)
        if video:
            video.status = "failed"
            video.error_message = str(e)
            video.save()
            
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass

            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=2 ** self.request.retries)

        return {"error": str(e), "status": "failed"}


def _extract_audio_with_ffmpeg(video_path: str, output_dir: str) -> str:
    audio_path = os.path.join(output_dir, "audio_temp.wav")
    ffmpeg_path = getattr(settings, "FFMPEG_PATH", "ffmpeg")
    max_seconds = getattr(settings, "WHISPER_MAX_AUDIO_SECONDS", None)
    
    cmd = [
        ffmpeg_path, "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", video_path,
        # Seleciona apenas 1 stream de áudio (se existir). Evita pegar streams estranhas/corrompidas.
        "-map", "0:a:0?",
        "-vn",
        # Tenta ignorar erros de decode em mídias com áudio quebrado.
        "-err_detect", "ignore_err",
        "-fflags", "+discardcorrupt",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    if isinstance(max_seconds, (int, float)) and max_seconds and max_seconds > 0:
        # Coloca -t antes do output para limitar o processamento.
        cmd.insert(-1, str(float(max_seconds)))
        cmd.insert(-1, "-t")

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return audio_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Erro FFmpeg áudio: {e.stderr.decode() if e.stderr else str(e)}")


def _transcribe_with_whisper(audio_path: str) -> dict:
    try:
        import whisper
        import torch
    except ImportError:
        raise Exception("Instale: pip install openai-whisper torch")

    model_size = getattr(settings, "WHISPER_MODEL")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Carregando Whisper modelo '{model_size}' em '{device}'...")
    
    try:
        model = whisper.load_model(model_size, device=device)

        whisper_word_timestamps = bool(getattr(settings, "WHISPER_WORD_TIMESTAMPS", True))

        use_fp16 = bool(getattr(settings, "WHISPER_FP16", True)) if device == "cuda" else False

        result = model.transcribe(
            audio_path,
            word_timestamps=whisper_word_timestamps,
            beam_size=int(getattr(settings, "WHISPER_BEAM_SIZE", 1)),
            best_of=int(getattr(settings, "WHISPER_BEST_OF", 1)),
            fp16=use_fp16,
        )

    except Exception as e:
        if device == "cuda":
            torch.cuda.empty_cache()
        raise Exception(f"Falha interna Whisper: {e}")

    segments = result.get("segments", [])
    full_text = result.get("text", "").strip()
    language = result.get("language", "en")

    structured_segments = []
    
    for seg in segments:
        words = []
        if "words" in seg:
            for w in seg["words"]:
                words.append({
                    "word": w["word"].strip(),
                    "start": w["start"],
                    "end": w["end"],
                    "score": w.get("probability", 0)
                })
        
        structured_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "words": words
        })

    if device == "cuda":
        del model
        torch.cuda.empty_cache()

    return {
        "full_text": full_text,
        "segments": structured_segments,
        "language": language,
        "confidence_score": 95
    }


def _configure_gemini() -> None:
    global _gemini_configured
    if _gemini_configured:
        return

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        raise Exception("GEMINI_API_KEY não configurada")

    genai.configure(api_key=api_key)
    _gemini_configured = True


def _refine_transcript_with_gemini(transcript_data: dict) -> dict:
    _configure_gemini()

    segments = transcript_data.get("segments") or []
    language = (transcript_data.get("language") or "").lower()

    max_segments = int(getattr(settings, "GEMINI_REFINE_MAX_SEGMENTS", 120) or 120)
    segments_slice = segments[:max_segments]

    input_segments = []
    for i, seg in enumerate(segments_slice):
        input_segments.append(
            {
                "i": i,
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", ""),
            }
        )

    response_schema = {
        "type": "object",
        "properties": {
            "domain": {"type": "string"},
            "language": {"type": "string"},
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "i": {"type": "integer"},
                        "text": {"type": "string"},
                    },
                    "required": ["i", "text"],
                },
            },
        },
        "required": ["domain", "language", "segments"],
    }

    base_prompt_pt = """
Você é um revisor de transcrições expert (Português).

Objetivo:
- Primeiro inferir o CONTEXTO/DOMÍNIO da conversa (ex: negócios, saúde, estudos, espaço, medicina, produtividade, programação, marketing, finanças, fitness, etc.).
- Em seguida, corrigir termos que o Whisper errou por causa de gírias, jargões, palavreado, metáforas ou nomes próprios.

Regras críticas:
1) NÃO altere timestamps. Eles já estão corretos. Você só pode reescrever o campo "text".
2) Preserve o sentido original e o tom. Não censure palavrões; apenas corrija grafia/termos.
3) Seja conservador: se não tiver certeza da correção, mantenha o original.
4) Não invente conteúdo que não foi falado.
5) Retorne SOMENTE JSON conforme o schema.

Entrada: lista de segmentos com índice i e seus textos.
Saída: para cada i, retorne "text" revisado.
"""

    base_prompt_en = """
You are an expert transcript editor.

Goal:
- First infer the conversation domain/context (business, health, studies, space, medicine, productivity, programming, etc.).
- Then fix misrecognized words caused by slang, jargon, metaphors, or proper nouns.

Critical rules:
1) Do NOT change timestamps. Only rewrite the "text" fields.
2) Preserve meaning and tone. Do not censor.
3) Be conservative: if unsure, keep the original.
4) Do not invent content.
5) Return ONLY JSON matching the schema.
"""

    prompt = base_prompt_pt if language.startswith("pt") else base_prompt_en
    payload = {
        "segments": input_segments,
    }

    model_name = getattr(settings, "GEMINI_REFINE_MODEL", "gemini-2.5-flash-lite")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        f"{prompt}\n\nSEGMENTS JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=float(getattr(settings, "GEMINI_REFINE_TEMPERATURE", 0.2) or 0.2),
        ),
    )

    refined = json.loads(response.text or "{}")
    refined_segments = refined.get("segments") or []
    by_i = {int(s.get("i")): (s.get("text") or "") for s in refined_segments if s.get("i") is not None}

    # Aplica apenas nos textos (mantendo start/end/words intocados)
    out_segments = list(segments)
    for i in range(min(len(segments_slice), len(out_segments))):
        new_text = by_i.get(i)
        if isinstance(new_text, str) and new_text.strip():
            out_segments[i] = {
                **out_segments[i],
                "text": new_text.strip(),
            }

    full_text = " ".join([(s.get("text") or "").strip() for s in out_segments]).strip()
    return {
        **transcript_data,
        "segments": out_segments,
        "full_text": full_text,
        "refine_meta": {
            "provider": "gemini",
            "model": model_name,
            "domain": refined.get("domain"),
            "language": refined.get("language") or transcript_data.get("language"),
            "segments_refined": len(out_segments[:max_segments]),
        },
    }


def _save_srt_file(transcript_data: dict, srt_path: str) -> None:
    segments = transcript_data.get("segments", [])
    
    def format_time(seconds):
        millis = int((seconds % 1) * 1000)
        seconds = int(seconds)
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            text = seg["text"].replace("\n", " ")
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
