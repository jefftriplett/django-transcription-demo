from django.db import models


class Transcript(models.Model):
    """Model to store YouTube video transcripts with SRT and plain text formats."""

    youtube_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="YouTube video ID (e.g., 'dQw4w9WgXcQ')",
    )
    srt_content = models.TextField(
        blank=True,
        help_text="SubRip subtitle format content",
    )
    text_content = models.TextField(
        blank=True,
        help_text="Plain text transcript content",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transcript"
        verbose_name_plural = "Transcripts"

    def __str__(self):
        return f"Transcript for YouTube ID: {self.youtube_id}"

    @property
    def youtube_url(self):
        """Return the full YouTube URL for this video."""
        return f"https://www.youtube.com/watch?v={self.youtube_id}"
