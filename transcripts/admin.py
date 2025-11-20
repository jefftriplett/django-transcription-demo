from django.contrib import admin

from .models import Transcript, SRTSegment, SearchConfig


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


@admin.register(SRTSegment)
class SRTSegmentAdmin(admin.ModelAdmin):
    list_display = ["transcript", "segment_index", "start_time", "end_time", "text_preview"]
    list_filter = ["transcript", "created_at"]
    search_fields = ["text", "youtube_id"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Preview")
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text


@admin.register(SearchConfig)
class SearchConfigAdmin(admin.ModelAdmin):
    list_display = ["default_search_type", "fts_weight", "trigram_weight", "vector_weight"]
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        return not SearchConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
