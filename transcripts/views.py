from django.contrib.postgres.search import SearchQuery, SearchRank
from django.shortcuts import get_object_or_404, render

from .models import Transcript


def homepage(request):
    """Homepage with search functionality for transcripts using PostgreSQL Full Text Search."""
    query = request.GET.get("q", "").strip()
    transcripts = []

    if query:
        # Use PostgreSQL Full Text Search with the pre-computed search_vector field
        search_query = SearchQuery(query, search_type="websearch", config="english")

        transcripts = (
            Transcript.objects.annotate(
                rank=SearchRank("search_vector", search_query),
            )
            .filter(search_vector=search_query)
            .order_by("-rank")
        )

        # Print raw SQL to console for debugging
        print("\n" + "=" * 80)
        print("SEARCH SQL QUERY:")
        print("=" * 80)
        print(transcripts.query)
        print("=" * 80 + "\n")

    context = {
        "query": query,
        "transcripts": transcripts,
    }
    return render(request, "transcripts/homepage.html", context)


def transcript_detail(request, youtube_id):
    """Detail view for a single transcript."""
    transcript = get_object_or_404(Transcript, youtube_id=youtube_id)

    context = {
        "transcript": transcript,
    }
    return render(request, "transcripts/detail.html", context)
