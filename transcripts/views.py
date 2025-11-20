from django.shortcuts import get_object_or_404, render

from .models import Transcript, SRTSegment
from .search import search_transcripts, search_segments


def homepage(request):
    """Homepage with search functionality for transcripts using FTS or Trigram search."""
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", "fts")  # 'fts' or 'trigram'
    transcripts = []
    segments = []

    if query:
        # Search transcripts using specified search type
        transcripts = search_transcripts(query)

        # If segments exist, also search them with the specified method
        if search_type == "trigram":
            segments = search_segments(query, search_type="trigram")
        elif search_type == "fts":
            segments = search_segments(query, search_type="fts")

        # Print raw SQL to console for debugging
        print("\n" + "=" * 80)
        print(f"SEARCH QUERY: '{query}' (search_type: {search_type})")
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
        "search_type": search_type,
        "transcripts": transcripts,
        "segments": segments,
    }
    return render(request, "transcripts/homepage.html", context)


def transcript_detail(request, youtube_id):
    """Detail view for a single transcript with segment search."""
    transcript = get_object_or_404(Transcript, youtube_id=youtube_id)
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("search_type", None)
    segments = []

    if query:
        # Search segments within this transcript
        all_segments = search_segments(query, search_type=search_type)
        segments = all_segments.filter(transcript=transcript)

    context = {
        "transcript": transcript,
        "query": query,
        "search_type": search_type,
        "segments": segments,
    }
    return render(request, "transcripts/detail.html", context)
