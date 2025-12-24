import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("klipai")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Configuração de filas por etapa com prioridades
app.conf.task_queues = {
    # Ingestion
    "video.ingestion": {"exchange": "video", "routing_key": "ingestion"},
    
    # Download (por plano)
    "video.download.starter": {"exchange": "video", "routing_key": "download.starter", "priority": 1},
    "video.download.business": {"exchange": "video", "routing_key": "download.business", "priority": 10},
    
    # Normalize (por plano)
    "video.normalize.starter": {"exchange": "video", "routing_key": "normalize.starter", "priority": 1},
    "video.normalize.business": {"exchange": "video", "routing_key": "normalize.business", "priority": 10},
    
    # Transcribe (por plano)
    "video.transcribe.starter": {"exchange": "video", "routing_key": "transcribe.starter", "priority": 1},
    "video.transcribe.business": {"exchange": "video", "routing_key": "transcribe.business", "priority": 10},
    
    # Analyze (por plano)
    "video.analyze.starter": {"exchange": "video", "routing_key": "analyze.starter", "priority": 1},
    "video.analyze.business": {"exchange": "video", "routing_key": "analyze.business", "priority": 10},
    
    # Classify (por plano)
    "video.classify.starter": {"exchange": "video", "routing_key": "classify.starter", "priority": 1},
    "video.classify.business": {"exchange": "video", "routing_key": "classify.business", "priority": 10},
    
    # Select (por plano)
    "video.select.starter": {"exchange": "video", "routing_key": "select.starter", "priority": 1},
    "video.select.business": {"exchange": "video", "routing_key": "select.business", "priority": 10},
    
    # Reframe (por plano)
    "video.reframe.starter": {"exchange": "video", "routing_key": "reframe.starter", "priority": 1},
    "video.reframe.business": {"exchange": "video", "routing_key": "reframe.business", "priority": 10},
    
    # Scoring (por plano)
    "video.scoring.starter": {"exchange": "video", "routing_key": "scoring.starter", "priority": 1},
    "video.scoring.business": {"exchange": "video", "routing_key": "scoring.business", "priority": 10},
    
    # Clip (por plano)
    "video.clip.starter": {"exchange": "video", "routing_key": "clip.starter", "priority": 1},
    "video.clip.business": {"exchange": "video", "routing_key": "clip.business", "priority": 10},
    
    # Caption (por plano)
    "video.caption.starter": {"exchange": "video", "routing_key": "caption.starter", "priority": 1},
    "video.caption.business": {"exchange": "video", "routing_key": "caption.business", "priority": 10},
    
    # Cron jobs
    "cron.credits": {"exchange": "cron", "routing_key": "credits"},
    "cron.cleanup": {"exchange": "cron", "routing_key": "cleanup"},
}

app.conf.task_routes = {
    # Download
    "clips.tasks.download_video_task": {"queue": "video.download.starter"},
    
    # Normalize
    "clips.tasks.normalize_video_task": {"queue": "video.normalize.starter"},
    
    # Transcribe
    "clips.tasks.transcribe_video_task": {"queue": "video.transcribe.starter"},
    
    # Analyze
    "clips.tasks.analyze_semantic_task": {"queue": "video.analyze.starter"},
    
    # Classify
    "clips.tasks.embed_classify_task": {"queue": "video.classify.starter"},
    
    # Select
    "clips.tasks.select_clips_task": {"queue": "video.select.starter"},
    
    # Reframe
    "clips.tasks.reframe_video_task": {"queue": "video.reframe.starter"},
    
    # Scoring
    "clips.tasks.clip_scoring_task": {"queue": "video.scoring.starter"},
    
    # Caption
    "clips.tasks.caption_clips_task": {"queue": "video.caption.starter"},
    
    # Clip
    "clips.tasks.clip_generation_task": {"queue": "video.clip.starter"},
    
    # Post
    "clips.tasks.post_to_social_task": {"queue": "default"},
}

app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1

app.conf.task_time_limit = int(os.getenv("CELERY_TASK_TIME_LIMIT", str(90 * 60)))
app.conf.task_soft_time_limit = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", str(85 * 60)))
