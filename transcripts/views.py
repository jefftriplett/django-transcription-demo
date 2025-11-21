from django.shortcuts import get_object_or_404, render

from .models import Transcript, SearchConfig
from .search import search_transcripts, search_segments


def homepage(request):
    """Homepage with search functionality for transcripts using configured search methods."""
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", None)
    transcripts = []
    segments = []
    warning_message = None

    config = SearchConfig.objects.first() or SearchConfig()

    if query:
        # Validate requested search type is enabled
        if search_type and not config.is_method_enabled(search_type):
            # Use default search type if requested one is disabled
            warning_message = (
                f"Search method '{search_type}' is disabled. Using '{config.default_search_type}' instead."
            )
            search_type = config.default_search_type

        # Search transcripts using specified search type
        transcripts = search_transcripts(query)

        # Search segments with the specified method
        segments = search_segments(query, search_type=search_type)

        # Print raw SQL to console for debugging
        print("\n" + "=" * 80)
        print(f"SEARCH QUERY: '{query}' (search_type: {search_type})")
        print(f"ENABLED METHODS: {', '.join(config.get_enabled_methods())}")
        print("=" * 80)
        if transcripts:
            print("TRANSCRIPT SEARCH SQL:")
            print(transcripts.query)
        if segments:
            print("\nSEGMENT SEARCH SQL:")
            print(segments.query)
        print("=" * 80 + "\n")

    context = {
        "query": query,
        "search_type": search_type or config.default_search_type,
        "transcripts": transcripts,
        "segments": segments,
        "config": config,
        "warning_message": warning_message,
    }
    return render(request, "transcripts/homepage.html", context)


def transcript_detail(request, youtube_id):
    """Detail view for a single transcript with segment search."""
    transcript = get_object_or_404(Transcript, youtube_id=youtube_id)
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", None)
    segments = []
    warning_message = None

    config = SearchConfig.objects.first() or SearchConfig()

    if query:
        # Validate requested search type is enabled
        if search_type and not config.is_method_enabled(search_type):
            # Use default search type if requested one is disabled
            warning_message = (
                f"Search method '{search_type}' is disabled. Using '{config.default_search_type}' instead."
            )
            search_type = config.default_search_type

        # Search segments within this transcript
        all_segments = search_segments(query, search_type=search_type)
        segments = all_segments.filter(transcript=transcript)

    context = {
        "transcript": transcript,
        "query": query,
        "search_type": search_type or config.default_search_type,
        "segments": segments,
        "config": config,
        "warning_message": warning_message,
    }
    return render(request, "transcripts/detail.html", context)
