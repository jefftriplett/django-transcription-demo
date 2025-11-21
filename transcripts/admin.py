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
    list_display = [
        "default_search_type",
        "search_methods_status",
        "fts_weight",
        "trigram_weight",
        "vector_weight",
    ]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (
            "Search Method Selection",
            {
                "fields": ["default_search_type"],
                "description": "Choose the default search method to use when no specific type is requested.",
            },
        ),
        (
            "Enable/Disable Search Methods",
            {
                "fields": ["fts_enabled", "trigram_enabled", "vector_enabled"],
                "description": "Control which search methods are available. At least one method must be enabled.",
            },
        ),
        (
            "Search Method Weights",
            {
                "fields": ["fts_weight", "trigram_weight", "vector_weight"],
                "description": "Adjust the relative importance of each search method in hybrid search results.",
            },
        ),
        (
            "Metadata",
            {
                "fields": ["created_at", "updated_at"],
            },
        ),
    ]

    @admin.display(description="Enabled Methods")
    def search_methods_status(self, obj):
        """Display which search methods are enabled."""
        methods = []
        if obj.fts_enabled:
            methods.append("FTS")
        if obj.trigram_enabled:
            methods.append("Trigram")
        if obj.vector_enabled:
            methods.append("Vector")
        return ", ".join(methods) if methods else "None"

    def has_add_permission(self, request):
        return not SearchConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
