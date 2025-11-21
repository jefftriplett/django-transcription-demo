"""
Search utilities for transcripts with support for Full Text Search, Trigram Search, Vector Search, and Hybrid approaches.
"""

from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import Cast, Greatest
from sentence_transformers import SentenceTransformer

from .models import SRTSegment, SearchConfig, Transcript

# Initialize embedding model
_embedding_model = None


def get_embedding_model():
    """Get or initialize the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_embedding(text):
    """Generate embedding for a text string."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


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


def vector_search_segments(query):
    """
    Search SRTSegment using semantic similarity with vector embeddings.
    Uses pgvector cosine similarity to find semantically similar segments.
    Returns segments ordered by similarity score.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    query = query.strip()
    query_embedding = get_embedding(query)

    # Use Django ORM to query with pgvector cosine similarity
    # The <-> operator performs cosine distance, so we negate it for similarity
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, (1 - (embedding <-> %s::vector)) as similarity
            FROM transcripts_srtsegment
            WHERE embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT 100
            """,
            [str(query_embedding)],
        )
        result_ids = [row[0] for row in cursor.fetchall()]

    if not result_ids:
        return SRTSegment.objects.none()

    # Fetch segments and preserve order
    segments_dict = {seg.id: seg for seg in SRTSegment.objects.filter(id__in=result_ids)}
    return SRTSegment.objects.filter(id__in=result_ids).order_by(
        "id"
    )  # Return in order they were found


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


def vector_search_segments(query):
    """
    Search SRTSegment using vector embeddings for semantic search.
    Currently a placeholder - implementation requires embedding generation.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    # Placeholder for vector search implementation
    # Would require:
    # 1. Converting query to embedding using same model as stored embeddings
    # 2. Computing similarity between query embedding and stored embeddings
    # 3. Returning segments ordered by similarity score
    return SRTSegment.objects.none()


def hybrid_search_segments(query):
    """
    Hybrid search combining enabled search methods with weighted scoring.
    Only uses search methods that are enabled in SearchConfig.
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    config = get_search_config()
    query = query.strip()
    enabled_methods = config.get_enabled_methods()

    if not enabled_methods:
        return SRTSegment.objects.none()

    combined_ids = set()

    # Trigram search if enabled
    if "trigram" in enabled_methods:
        trigram_results = trigram_search_segments(query)
        combined_ids.update(trigram_results.values_list("id", flat=True))

    # FTS search if enabled
    if "fts" in enabled_methods:
        fts_results = fts_search_segments(query)
        combined_ids.update(fts_results.values_list("id", flat=True))

    # Vector search if enabled (when implemented)
    if "vector" in enabled_methods:
        vector_results = vector_search_segments(query)
        combined_ids.update(vector_results.values_list("id", flat=True))

    if not combined_ids:
        return SRTSegment.objects.none()

    # Annotate with scores from enabled methods
    results = SRTSegment.objects.filter(id__in=combined_ids)

    if "trigram" in enabled_methods:
        results = results.annotate(
            trigram_score=TrigramSimilarity("text", query),
        )
    else:
        results = results.annotate(
            trigram_score=Value(0.0, output_field=FloatField()),
        )

    # Calculate weighted score based on enabled methods
    score_components = []
    if "trigram" in enabled_methods:
        score_components.append(F("trigram_score") * Value(config.trigram_weight))

    if score_components:
        results = results.annotate(
            combined_score=Cast(
                Greatest(*score_components, output_field=FloatField()),
                FloatField(),
            )
        )
    else:
        results = results.annotate(
            combined_score=Value(0.0, output_field=FloatField()),
        )

    return results.order_by("-combined_score")


def search_segments(query, search_type=None):
    """
    Search segments using the configured search type.

    Args:
        query: Search query string
        search_type: Type of search ('fts', 'trigram', 'vector', 'hybrid').
                     If None, uses the default from SearchConfig.

    Returns:
        QuerySet of matching SRTSegment objects ordered by relevance
    """
    if not query or not query.strip():
        return SRTSegment.objects.none()

    config = get_search_config()

    if search_type is None:
        search_type = config.default_search_type

    # Validate that the requested search type is enabled
    if search_type != "hybrid":
        if not config.is_method_enabled(search_type):
            # Fall back to hybrid if requested method is disabled
            search_type = "hybrid"

    if search_type == "trigram" and config.trigram_enabled:
        return trigram_search_segments(query)
    elif search_type == "fts" and config.fts_enabled:
        return fts_search_segments(query)
    elif search_type == "vector":
        return vector_search_segments(query)
    else:  # hybrid or fallback
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
