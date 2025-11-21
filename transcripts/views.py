from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render

from .models import Transcript, SearchConfig
from .search import search_transcripts, search_segments


def homepage(request):
    """Homepage with search functionality for transcripts using configured search methods."""
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", None)
    page = request.GET.get("page", 1)
    transcripts = []
    segments = []
    transcripts_page = None
    segments_page = None
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

        # Paginate transcripts
        transcripts_paginator = Paginator(transcripts, 10)  # 10 transcripts per page
        try:
            transcripts_page = transcripts_paginator.page(page)
        except PageNotAnInteger:
            transcripts_page = transcripts_paginator.page(1)
        except EmptyPage:
            transcripts_page = transcripts_paginator.page(transcripts_paginator.num_pages)

        # Paginate segments
        segments_paginator = Paginator(segments, 20)  # 20 segments per page
        try:
            segments_page = segments_paginator.page(page)
        except PageNotAnInteger:
            segments_page = segments_paginator.page(1)
        except EmptyPage:
            segments_page = segments_paginator.page(segments_paginator.num_pages)

    context = {
        "query": query,
        "search_type": search_type or config.default_search_type,
        "transcripts": transcripts_page,
        "segments": segments_page,
        "config": config,
        "warning_message": warning_message,
    }
    return render(request, "transcripts/homepage.html", context)


def transcript_detail(request, youtube_id):
    """Detail view for a single transcript with segment search."""
    transcript = get_object_or_404(Transcript, youtube_id=youtube_id)
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", None)
    page = request.GET.get("page", 1)
    segments = []
    segments_page = None
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

        # Paginate segments
        segments_paginator = Paginator(segments, 20)  # 20 segments per page
        try:
            segments_page = segments_paginator.page(page)
        except PageNotAnInteger:
            segments_page = segments_paginator.page(1)
        except EmptyPage:
            segments_page = segments_paginator.page(segments_paginator.num_pages)

    context = {
        "transcript": transcript,
        "query": query,
        "search_type": search_type or config.default_search_type,
        "segments": segments_page,
        "config": config,
        "warning_message": warning_message,
    }
    return render(request, "transcripts/detail.html", context)
