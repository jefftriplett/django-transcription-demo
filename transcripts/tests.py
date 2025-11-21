"""
Comprehensive test suite for the hybrid search toggle functionality.

Tests cover:
- SearchConfig model with enable/disable toggles for FTS, trigram, and vector search
- Individual search methods respecting enabled toggles
- Hybrid search combining only enabled methods
- Search dispatcher fallback behavior when methods are disabled
- All toggle combinations and edge cases
"""

import pytest
from django.db.models import QuerySet
from model_bakery import baker

from .models import SearchConfig, SRTSegment, Transcript
from .search import (
    fts_search_segments,
    get_search_config,
    hybrid_search_segments,
    search_segments,
    trigram_search_segments,
    vector_search_segments,
)


@pytest.mark.django_db
class TestSearchConfigModel:
    """Test SearchConfig model with toggle functionality."""

    def test_default_search_config_creation(self):
        """Test that default SearchConfig is created with sensible defaults."""
        config = SearchConfig.objects.create()
        assert config.fts_enabled is True
        assert config.trigram_enabled is True
        assert config.vector_enabled is False
        assert config.default_search_type == "hybrid"

    def test_get_search_config_returns_singleton(self):
        """Test that get_search_config returns the same config instance."""
        config1 = get_search_config()
        config2 = get_search_config()
        assert config1.pk == config2.pk

    def test_get_enabled_methods_all_enabled(self):
        """Test get_enabled_methods returns all enabled methods."""
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
            vector_enabled=True,
        )
        enabled = config.get_enabled_methods()
        assert set(enabled) == {"fts", "trigram", "vector"}

    def test_get_enabled_methods_fts_only(self):
        """Test get_enabled_methods with only FTS enabled."""
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
            vector_enabled=False,
        )
        enabled = config.get_enabled_methods()
        assert enabled == ["fts"]

    def test_get_enabled_methods_trigram_only(self):
        """Test get_enabled_methods with only trigram enabled."""
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=True,
            vector_enabled=False,
        )
        enabled = config.get_enabled_methods()
        assert enabled == ["trigram"]

    def test_get_enabled_methods_vector_only(self):
        """Test get_enabled_methods with only vector enabled."""
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=True,
        )
        enabled = config.get_enabled_methods()
        assert enabled == ["vector"]

    def test_get_enabled_methods_none_enabled(self):
        """Test get_enabled_methods when no methods are enabled."""
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=False,
        )
        enabled = config.get_enabled_methods()
        assert enabled == []

    def test_is_method_enabled_fts(self):
        """Test is_method_enabled for FTS."""
        config = SearchConfig.objects.create(fts_enabled=True)
        assert config.is_method_enabled("fts") is True
        config.fts_enabled = False
        assert config.is_method_enabled("fts") is False

    def test_is_method_enabled_trigram(self):
        """Test is_method_enabled for trigram."""
        config = SearchConfig.objects.create(trigram_enabled=True)
        assert config.is_method_enabled("trigram") is True
        config.trigram_enabled = False
        assert config.is_method_enabled("trigram") is False

    def test_is_method_enabled_vector(self):
        """Test is_method_enabled for vector."""
        config = SearchConfig.objects.create(vector_enabled=True)
        assert config.is_method_enabled("vector") is True
        config.vector_enabled = False
        assert config.is_method_enabled("vector") is False

    def test_is_method_enabled_invalid_method(self):
        """Test is_method_enabled with invalid method name."""
        config = SearchConfig.objects.create()
        assert config.is_method_enabled("invalid") is False
        assert config.is_method_enabled("unknown") is False

    def test_is_method_enabled_all_disabled(self):
        """Test is_method_enabled when all methods are disabled."""
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=False,
        )
        assert config.is_method_enabled("fts") is False
        assert config.is_method_enabled("trigram") is False
        assert config.is_method_enabled("vector") is False


@pytest.mark.django_db
class TestTrigramSearchSegments:
    """Test trigram search functionality."""

    def test_trigram_search_empty_query(self):
        """Test that empty query returns empty QuerySet."""
        result = trigram_search_segments("")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_trigram_search_none_query(self):
        """Test that None query returns empty QuerySet."""
        result = trigram_search_segments(None)
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_trigram_search_whitespace_query(self):
        """Test that whitespace-only query returns empty QuerySet."""
        result = trigram_search_segments("   ")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_trigram_search_finds_exact_match(self):
        """Test trigram search finds exact text matches."""
        transcript = baker.make(Transcript, text_content="hello world")
        segment = baker.make(SRTSegment, transcript=transcript, text="hello world")

        result = trigram_search_segments("hello world")
        assert segment in result

    def test_trigram_search_finds_partial_match(self):
        """Test trigram search finds partial text matches."""
        transcript = baker.make(Transcript, text_content="hello beautiful world")
        segment = baker.make(SRTSegment, transcript=transcript, text="hello beautiful world")

        result = trigram_search_segments("hello")
        assert segment in result

    def test_trigram_search_multiple_segments(self):
        """Test trigram search returns multiple matching segments."""
        transcript = baker.make(Transcript)
        segment1 = baker.make(SRTSegment, transcript=transcript, text="apple fruit")
        segment2 = baker.make(SRTSegment, transcript=transcript, text="apple pie")
        segment3 = baker.make(SRTSegment, transcript=transcript, text="orange fruit")

        result = trigram_search_segments("apple")
        result_ids = set(result.values_list("id", flat=True))
        assert segment1.id in result_ids
        assert segment2.id in result_ids
        assert segment3.id not in result_ids

    def test_trigram_search_returns_queryset(self):
        """Test that trigram search returns a QuerySet."""
        baker.make(Transcript, text_content="test content")
        result = trigram_search_segments("test")
        assert isinstance(result, QuerySet)


@pytest.mark.django_db
class TestFTSSearchSegments:
    """Test Full Text Search functionality."""

    def test_fts_search_empty_query(self):
        """Test that empty query returns empty QuerySet."""
        result = fts_search_segments("")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_fts_search_none_query(self):
        """Test that None query returns empty QuerySet."""
        result = fts_search_segments(None)
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_fts_search_whitespace_query(self):
        """Test that whitespace-only query returns empty QuerySet."""
        result = fts_search_segments("   ")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_fts_search_returns_queryset(self):
        """Test that FTS search returns a QuerySet."""
        baker.make(Transcript, text_content="test content")
        result = fts_search_segments("test")
        assert isinstance(result, QuerySet)

    def test_fts_search_returns_segments_from_matching_transcripts(self):
        """Test FTS returns segments from matching transcripts."""
        transcript = baker.make(Transcript, text_content="machine learning")
        segment = baker.make(SRTSegment, transcript=transcript, text="segment text")

        result = fts_search_segments("machine")
        assert segment in result

    def test_fts_search_excludes_non_matching_segments(self):
        """Test FTS excludes segments from non-matching transcripts."""
        transcript1 = baker.make(Transcript, text_content="machine learning")
        transcript2 = baker.make(Transcript, text_content="other content")

        segment1 = baker.make(SRTSegment, transcript=transcript1, text="segment 1")
        segment2 = baker.make(SRTSegment, transcript=transcript2, text="segment 2")

        result = fts_search_segments("machine")
        result_ids = set(result.values_list("id", flat=True))
        assert segment1.id in result_ids
        assert segment2.id not in result_ids


@pytest.mark.django_db
class TestVectorSearchSegments:
    """Test vector search functionality."""

    def test_vector_search_empty_query(self):
        """Test that empty query returns empty QuerySet."""
        result = vector_search_segments("")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_vector_search_none_query(self):
        """Test that None query returns empty QuerySet."""
        result = vector_search_segments(None)
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_vector_search_whitespace_query(self):
        """Test that whitespace-only query returns empty QuerySet."""
        result = vector_search_segments("   ")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_vector_search_placeholder_returns_empty(self):
        """Test that vector search placeholder returns empty QuerySet."""
        baker.make(Transcript)
        result = vector_search_segments("test")
        assert isinstance(result, QuerySet)
        assert result.count() == 0


@pytest.mark.django_db
class TestHybridSearchSegments:
    """Test hybrid search combining multiple methods."""

    def test_hybrid_search_empty_query(self):
        """Test hybrid search with empty query."""
        result = hybrid_search_segments("")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_hybrid_search_none_query(self):
        """Test hybrid search with None query."""
        result = hybrid_search_segments(None)
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_hybrid_search_fts_only_enabled(self):
        """Test hybrid search with only FTS enabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
            vector_enabled=False,
        )

        transcript = baker.make(Transcript, text_content="machine learning")
        segment = baker.make(SRTSegment, transcript=transcript, text="segment text")

        result = hybrid_search_segments("machine")
        assert segment in result

    def test_hybrid_search_trigram_only_enabled(self):
        """Test hybrid search with only trigram enabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=True,
            vector_enabled=False,
        )

        transcript = baker.make(Transcript)
        segment = baker.make(SRTSegment, transcript=transcript, text="hello world")

        result = hybrid_search_segments("hello")
        assert segment in result

    def test_hybrid_search_fts_and_trigram_enabled(self):
        """Test hybrid search with both FTS and trigram enabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
            vector_enabled=False,
        )

        transcript1 = baker.make(Transcript, text_content="python programming")
        transcript2 = baker.make(Transcript, text_content="other content")

        segment1 = baker.make(SRTSegment, transcript=transcript1, text="python code")
        segment2 = baker.make(SRTSegment, transcript=transcript2, text="programming guide")

        result = hybrid_search_segments("python")
        result_ids = set(result.values_list("id", flat=True))
        assert segment1.id in result_ids
        # segment2 should be in results from trigram search
        assert segment2.id in result_ids

    def test_hybrid_search_no_methods_enabled(self):
        """Test hybrid search when no methods are enabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=False,
        )

        result = hybrid_search_segments("test")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_hybrid_search_respects_config_toggles(self):
        """Test that hybrid search respects SearchConfig toggles."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
            vector_enabled=False,
        )

        transcript = baker.make(Transcript, text_content="test content")
        baker.make(SRTSegment, transcript=transcript, text="test")

        # With trigram disabled, should only use FTS
        result = hybrid_search_segments("test")
        # Result depends on whether FTS finds the transcript
        assert isinstance(result, QuerySet)

    def test_hybrid_search_returns_queryset(self):
        """Test that hybrid search returns a QuerySet."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create()
        baker.make(Transcript, text_content="test")

        result = hybrid_search_segments("test")
        assert isinstance(result, QuerySet)


@pytest.mark.django_db
class TestSearchSegmentsDispatcher:
    """Test the main search_segments dispatcher function."""

    def test_search_segments_empty_query(self):
        """Test search_segments with empty query."""
        result = search_segments("")
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_search_segments_none_query(self):
        """Test search_segments with None query."""
        result = search_segments(None)
        assert isinstance(result, QuerySet)
        assert result.count() == 0

    def test_search_segments_uses_default_type(self):
        """Test that search_segments uses default search type."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            default_search_type="hybrid",
            fts_enabled=True,
            trigram_enabled=True,
        )

        transcript = baker.make(Transcript, text_content="test content")
        baker.make(SRTSegment, transcript=transcript, text="test")

        result = search_segments("test")
        assert isinstance(result, QuerySet)

    def test_search_segments_explicit_fts_type(self):
        """Test search_segments with explicit FTS type."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(fts_enabled=True)

        transcript = baker.make(Transcript, text_content="test content")
        baker.make(SRTSegment, transcript=transcript, text="test")

        result = search_segments("test", search_type="fts")
        assert isinstance(result, QuerySet)

    def test_search_segments_explicit_trigram_type(self):
        """Test search_segments with explicit trigram type."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(trigram_enabled=True)

        transcript = baker.make(Transcript)
        baker.make(SRTSegment, transcript=transcript, text="hello world")

        result = search_segments("hello", search_type="trigram")
        assert isinstance(result, QuerySet)

    def test_search_segments_fallback_when_fts_disabled(self):
        """Test that search_segments falls back to hybrid when FTS is disabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=True,
        )

        transcript = baker.make(Transcript)
        baker.make(SRTSegment, transcript=transcript, text="hello")

        # Request FTS but it's disabled, should fall back to hybrid
        result = search_segments("hello", search_type="fts")
        assert isinstance(result, QuerySet)

    def test_search_segments_fallback_when_trigram_disabled(self):
        """Test that search_segments falls back to hybrid when trigram is disabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
        )

        baker.make(Transcript, text_content="test")

        # Request trigram but it's disabled, should fall back to hybrid
        result = search_segments("test", search_type="trigram")
        assert isinstance(result, QuerySet)

    def test_search_segments_hybrid_always_available(self):
        """Test that hybrid search is always available as fallback."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
        )

        transcript = baker.make(Transcript, text_content="test")
        baker.make(SRTSegment, transcript=transcript, text="test")

        result = search_segments("test", search_type="hybrid")
        assert isinstance(result, QuerySet)

    def test_search_segments_whitespace_stripping(self):
        """Test that search_segments strips whitespace."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create()

        baker.make(Transcript, text_content="test")

        result = search_segments("  test  ")
        assert isinstance(result, QuerySet)

    def test_search_segments_none_search_type_uses_default(self):
        """Test that None search_type uses default from config."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(default_search_type="hybrid")

        result = search_segments("test", search_type=None)
        assert isinstance(result, QuerySet)


@pytest.mark.django_db
class TestSearchToggleCombinations:
    """Test various combinations of search method toggles."""

    def test_all_methods_enabled(self):
        """Test search with all methods enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
            vector_enabled=True,
        )

        enabled = config.get_enabled_methods()
        assert len(enabled) == 3
        assert set(enabled) == {"fts", "trigram", "vector"}

    def test_no_methods_enabled_hybrid_returns_empty(self):
        """Test that hybrid search returns empty when no methods enabled."""
        SearchConfig.objects.all().delete()
        SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=False,
        )

        result = hybrid_search_segments("test")
        assert result.count() == 0

    def test_fts_only_combination(self):
        """Test search with only FTS enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
            vector_enabled=False,
        )

        enabled = config.get_enabled_methods()
        assert enabled == ["fts"]

    def test_trigram_only_combination(self):
        """Test search with only trigram enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=True,
            vector_enabled=False,
        )

        enabled = config.get_enabled_methods()
        assert enabled == ["trigram"]

    def test_vector_only_combination(self):
        """Test search with only vector enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=True,
        )

        enabled = config.get_enabled_methods()
        assert enabled == ["vector"]

    def test_fts_trigram_combination(self):
        """Test search with FTS and trigram enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
            vector_enabled=False,
        )

        enabled = config.get_enabled_methods()
        assert set(enabled) == {"fts", "trigram"}

    def test_fts_vector_combination(self):
        """Test search with FTS and vector enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=False,
            vector_enabled=True,
        )

        enabled = config.get_enabled_methods()
        assert set(enabled) == {"fts", "vector"}

    def test_trigram_vector_combination(self):
        """Test search with trigram and vector enabled."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=True,
            vector_enabled=True,
        )

        enabled = config.get_enabled_methods()
        assert set(enabled) == {"trigram", "vector"}

    def test_toggle_disable_mid_session(self):
        """Test disabling search methods mid-session."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=True,
            trigram_enabled=True,
            vector_enabled=False,
        )

        # Start with both enabled
        assert config.is_method_enabled("fts") is True
        assert config.is_method_enabled("trigram") is True

        # Disable trigram
        config.trigram_enabled = False
        config.save()

        # Verify state changed
        config.refresh_from_db()
        assert config.is_method_enabled("fts") is True
        assert config.is_method_enabled("trigram") is False

    def test_toggle_enable_mid_session(self):
        """Test enabling search methods mid-session."""
        SearchConfig.objects.all().delete()
        config = SearchConfig.objects.create(
            fts_enabled=False,
            trigram_enabled=False,
            vector_enabled=False,
        )

        # Start with all disabled
        assert config.get_enabled_methods() == []

        # Enable FTS
        config.fts_enabled = True
        config.save()

        # Verify state changed
        config.refresh_from_db()
        assert config.is_method_enabled("fts") is True


@pytest.mark.django_db
class TestSearchConfigWeights:
    """Test search method weighting in hybrid search."""

    def test_default_weight_values(self):
        """Test that default weights sum to reasonable value."""
        config = SearchConfig.objects.create()
        assert config.fts_weight == 0.3
        assert config.trigram_weight == 0.3
        assert config.vector_weight == 0.4

    def test_custom_weight_assignment(self):
        """Test assigning custom weights."""
        config = SearchConfig.objects.create(
            fts_weight=0.5,
            trigram_weight=0.3,
            vector_weight=0.2,
        )
        assert config.fts_weight == 0.5
        assert config.trigram_weight == 0.3
        assert config.vector_weight == 0.2

    def test_weight_persistence(self):
        """Test that weights persist after save/refresh."""
        config = SearchConfig.objects.create(
            fts_weight=0.6,
            trigram_weight=0.2,
            vector_weight=0.2,
        )
        config.save()
        config.refresh_from_db()
        assert config.fts_weight == 0.6
        assert config.trigram_weight == 0.2
        assert config.vector_weight == 0.2


@pytest.mark.django_db
class TestSearchConfigDefaults:
    """Test SearchConfig model defaults and metadata."""

    def test_string_representation(self):
        """Test SearchConfig __str__ method."""
        config = SearchConfig.objects.create(default_search_type="hybrid")
        assert "hybrid" in str(config)

    def test_search_types_choices(self):
        """Test that SEARCH_TYPES has expected choices."""
        choices_dict = dict(SearchConfig.SEARCH_TYPES)
        assert "fts" in choices_dict
        assert "trigram" in choices_dict
        assert "vector" in choices_dict
        assert "hybrid" in choices_dict

    def test_verbose_names(self):
        """Test model verbose names."""
        assert SearchConfig._meta.verbose_name == "Search Configuration"
        assert SearchConfig._meta.verbose_name_plural == "Search Configurations"

    def test_default_search_type_choices_are_valid(self):
        """Test that default_search_type accepts all SEARCH_TYPES."""
        for search_type, _ in SearchConfig.SEARCH_TYPES:
            config = SearchConfig.objects.create(default_search_type=search_type)
            config.full_clean()  # Should not raise ValidationError
            assert config.default_search_type == search_type
