from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
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

    # Full text search vector field
    search_vector = models.GeneratedField(
        expression=SearchVector("youtube_id", weight="A", config="english")
        + SearchVector("text_content", weight="B", config="english")
        + SearchVector("srt_content", weight="C", config="english"),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transcript"
        verbose_name_plural = "Transcripts"
        indexes = [
            GinIndex(fields=["search_vector"], name="transcript_search_idx"),
        ]

    def __str__(self):
        return f"Transcript for YouTube ID: {self.youtube_id}"

    @property
    def youtube_url(self):
        """Return the full YouTube URL for this video."""
        return f"https://www.youtube.com/watch?v={self.youtube_id}"


class SRTSegment(models.Model):
    """Model to store individual segments from transcripts with trigram search support."""

    youtube_id = models.CharField(
        max_length=20,
        db_index=True,
        help_text="YouTube video ID",
    )
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    segment_index = models.IntegerField(
        help_text="Index of this segment in the transcript",
    )
    start_time = models.CharField(
        max_length=12,
        help_text="Start time in HH:MM:SS format",
    )
    end_time = models.CharField(
        max_length=12,
        help_text="End time in HH:MM:SS format",
    )
    text = models.TextField(
        help_text="Segment text content",
    )
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vector embedding for semantic search",
    )
    embedding_model = models.CharField(
        max_length=50,
        default="",
        help_text="Model used to generate embedding",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["transcript", "segment_index"]
        verbose_name = "SRT Segment"
        verbose_name_plural = "SRT Segments"
        indexes = [
            GistIndex(fields=["text"], name="srtsegment_text_trgm_idx", opclasses=["gist_trgm_ops"]),
            models.Index(fields=["transcript", "segment_index"], name="transcripts_transcr_2a2581_idx"),
            models.Index(fields=["youtube_id"]),
        ]

    def __str__(self):
        return f"Segment {self.segment_index} ({self.start_time}-{self.end_time})"


class SearchConfig(models.Model):
    """Configuration for search behavior and weights."""

    SEARCH_TYPES = [
        ("fts", "Full Text Search"),
        ("trigram", "Trigram Search"),
        ("vector", "Vector/Semantic Search"),
        ("hybrid", "Hybrid Search"),
    ]

    default_search_type = models.CharField(
        max_length=20,
        choices=SEARCH_TYPES,
        default="hybrid",
        help_text="Default search type to use",
    )
    fts_weight = models.FloatField(
        default=0.3,
        help_text="Weight for Full Text Search results (0-1)",
    )
    trigram_weight = models.FloatField(
        default=0.3,
        help_text="Weight for Trigram Search results (0-1)",
    )
    vector_weight = models.FloatField(
        default=0.4,
        help_text="Weight for Vector/Semantic Search results (0-1)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Search Configuration"
        verbose_name_plural = "Search Configurations"

    def __str__(self):
        return f"Search Config ({self.default_search_type})"
