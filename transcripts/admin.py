from django.contrib import admin

from .models import Transcript


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ["youtube_id", "has_srt", "has_text", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["youtube_id"]
    readonly_fields = ["created_at", "updated_at", "youtube_url"]
    fieldsets = [
        (
            "YouTube Information",
            {
                "fields": ["youtube_id", "youtube_url"],
            },
        ),
        (
            "Transcript Content",
            {
                "fields": ["srt_content", "text_content"],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]

    @admin.display(boolean=True, description="Has SRT")
    def has_srt(self, obj):
        return bool(obj.srt_content)

    @admin.display(boolean=True, description="Has Text")
    def has_text(self, obj):
        return bool(obj.text_content)
