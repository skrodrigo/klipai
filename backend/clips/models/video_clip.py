from django.db import models


class VideoClip(models.Model):
    video = models.ForeignKey(
        "Video",
        related_name="clips",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    start_time = models.FloatField(default=0)
    end_time = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # type: ignore[override]
        return self.title
