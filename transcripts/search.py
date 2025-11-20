"""
Search utilities for transcripts with support for Full Text Search, Trigram Search, and Hybrid approaches.
"""

from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import Cast, Greatest

from .models import SRTSegment, SearchConfig, Transcript


def get_search_config():
    """Get the active search configuration or create defaults."""
    config, created = SearchConfig.objects.get_or_create(pk=1)
    return config


def trigram_search_segments(query):
    """
    Search SRTSegment using trigram similarity from pg_trgm extension.
    Returns segments ordered by similarity score.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    query = query.strip()
    return (
        SRTSegment.objects.annotate(
            similarity=TrigramSimilarity("text", query),
        )
        .filter(similarity__gt=0.05)  # Filter by minimum similarity threshold
        .order_by("-similarity")
    )


def fts_search_segments(query):
    """
    Search SRTSegment using trigram search (since text field doesn't support FTS lookup).
    For FTS on segments, we search the associated Transcript.
    Returns segments ordered by relevance.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    query = query.strip()
    search_query = SearchQuery(query, search_type="websearch", config="english")

    # Get matching transcripts using FTS
    matching_transcripts = Transcript.objects.filter(
        search_vector=search_query
    )

    # Return segments from matching transcripts
    return SRTSegment.objects.filter(
        transcript__in=matching_transcripts
    ).order_by("transcript", "segment_index")


def hybrid_search_segments(query):
    """
    Hybrid search combining trigram and full text search.
    Uses weighted scoring to rank results.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    config = get_search_config()
    query = query.strip()

    # Trigram search with similarity score
    trigram_results = trigram_search_segments(query)
    trigram_dict = {
        seg.id: seg for seg in trigram_results.values_list("id", flat=True)
    }

    # FTS search
    fts_results = fts_search_segments(query)
    fts_dict = {seg.id: seg for seg in fts_results.values_list("id", flat=True)}

    # Combine results with weighted scores
    combined_ids = set(trigram_dict.keys()) | set(fts_dict.keys())

    if not combined_ids:
        return SRTSegment.objects.none()

    # Annotate with combined score
    results = SRTSegment.objects.filter(id__in=combined_ids).annotate(
        trigram_score=TrigramSimilarity("text", query),
    )

    # Calculate weighted score
    results = results.annotate(
        combined_score=Cast(
            Greatest(
                F("trigram_score") * Value(config.trigram_weight),
                output_field=FloatField(),
            ),
            FloatField(),
        )
    )

    return results.order_by("-combined_score")


def search_segments(query, search_type=None):
    """
    Search segments using the configured search type.

    Args:
        query: Search query string
        search_type: Type of search ('fts', 'trigram', 'hybrid').
                     If None, uses the default from SearchConfig.

    Returns:
        QuerySet of matching SRTSegment objects ordered by relevance
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    if search_type is None:
        config = get_search_config()
        search_type = config.default_search_type

    if search_type == "trigram":
        return trigram_search_segments(query)
    elif search_type == "fts":
        return fts_search_segments(query)
    else:  # hybrid or default
        return hybrid_search_segments(query)


def search_transcripts(query, search_type=None):
    """
    Search transcripts using Full Text Search.
    Returns Transcript objects ordered by relevance.
    """
    if not query or not query.strip():
        return Transcript.objects.none()

    query = query.strip()
    search_query = SearchQuery(query, search_type="websearch", config="english")

    return (
        Transcript.objects.annotate(
            rank=SearchRank("search_vector", search_query),
        )
        .filter(search_vector=search_query)
        .order_by("-rank")
    )
