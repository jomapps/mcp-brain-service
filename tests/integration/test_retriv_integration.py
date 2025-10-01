"""Integration tests for Retriv service with real retriv library."""

import pytest
import os
import shutil
from pathlib import Path
from src.services.retriv_service import RetrivService


# Skip these tests if retriv is not installed
pytest.importorskip("retriv", reason="retriv package not installed")


@pytest.fixture
def test_index_path(tmp_path):
    """Create a temporary index path for testing."""
    index_path = tmp_path / "test_retriv_index"
    yield str(index_path)
    # Cleanup
    if index_path.exists():
        shutil.rmtree(index_path)


@pytest.fixture
def retriv_service(test_index_path):
    """Create a RetrivService instance with test index path."""
    return RetrivService(index_path=test_index_path)


@pytest.fixture
def aladdin_documents():
    """Sample Aladdin movie documents for testing."""
    return [
        {
            "id": "char_aladdin",
            "text": "Aladdin is a street-smart young man who wears a brown vest, purple pants, and a red fez. He has a pet monkey named Abu.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Aladdin",
                "category": "protagonist"
            }
        },
        {
            "id": "char_jasmine",
            "text": "Princess Jasmine wears a beautiful blue outfit with gold jewelry. She has long black hair and a pet tiger named Rajah.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Jasmine",
                "category": "protagonist"
            }
        },
        {
            "id": "char_genie",
            "text": "The Genie is a magical blue being with incredible cosmic powers. He can grant three wishes and loves to make jokes.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Genie",
                "category": "supporting"
            }
        },
        {
            "id": "scene_marketplace",
            "text": "Scene 3: Aladdin meets Jasmine in the bustling marketplace. He helps her escape from an angry merchant after she takes an apple for a hungry child.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "scene",
                "scene_number": 3,
                "location": "marketplace"
            }
        },
        {
            "id": "scene_cave",
            "text": "Scene 7: Aladdin enters the Cave of Wonders wearing his brown vest. He finds the magic lamp but Abu touches a forbidden treasure.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "scene",
                "scene_number": 7,
                "location": "cave_of_wonders"
            }
        },
        {
            "id": "char_jafar",
            "text": "Jafar is the evil royal vizier who wears black and red robes. He has a snake staff and seeks ultimate power.",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Jafar",
                "category": "antagonist"
            }
        }
    ]


class TestRetrivIntegrationBasic:
    """Basic integration tests with real retriv."""
    
    @pytest.mark.asyncio
    async def test_initialize_real_retriv(self, retriv_service):
        """Test initialization with real retriv library."""
        await retriv_service.initialize()
        
        assert retriv_service._initialized is True
        assert retriv_service.retriever is not None
    
    @pytest.mark.asyncio
    async def test_index_and_search_real(self, retriv_service, aladdin_documents):
        """Test indexing and searching with real retriv."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Search for "brown vest"
        results = await retriv_service.search("brown vest", top_k=3)
        
        assert len(results) > 0
        # Should find Aladdin character or cave scene
        result_ids = [r["id"] for r in results]
        assert "char_aladdin" in result_ids or "scene_cave" in result_ids


class TestRetrivHybridSearch:
    """Test hybrid search capabilities (BM25 + embeddings)."""
    
    @pytest.mark.asyncio
    async def test_keyword_matching(self, retriv_service, aladdin_documents):
        """Test that BM25 catches exact keyword matches."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Search with specific keywords
        results = await retriv_service.search("brown vest scene 7", top_k=5)
        
        assert len(results) > 0
        # Should rank scene_cave high due to exact matches
        top_result = results[0]
        assert "brown vest" in top_result["text"].lower() or "scene 7" in top_result["text"].lower()
    
    @pytest.mark.asyncio
    async def test_semantic_matching(self, retriv_service, aladdin_documents):
        """Test that embeddings catch semantic similarity."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Search with semantic query (no exact keywords)
        results = await retriv_service.search("magical being with powers", top_k=3)
        
        assert len(results) > 0
        # Should find Genie due to semantic similarity
        result_ids = [r["id"] for r in results]
        assert "char_genie" in result_ids
    
    @pytest.mark.asyncio
    async def test_hybrid_better_than_keyword_alone(self, retriv_service, aladdin_documents):
        """Test that hybrid search combines keyword + semantic."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Query that benefits from both keyword and semantic
        results = await retriv_service.search("Aladdin's clothing in scene 3", top_k=5)
        
        assert len(results) > 0
        # Should find both character description and scene
        result_ids = [r["id"] for r in results]
        # At least one of these should be in top results
        assert any(rid in result_ids for rid in ["char_aladdin", "scene_marketplace", "scene_cave"])


class TestRetrivFiltering:
    """Test filtering capabilities."""
    
    @pytest.mark.asyncio
    async def test_project_filter(self, retriv_service, aladdin_documents):
        """Test filtering by project_id."""
        # Add documents from different projects
        mixed_docs = aladdin_documents + [
            {
                "id": "other_char",
                "text": "A character from another movie",
                "metadata": {"project_id": "other_movie", "type": "character"}
            }
        ]
        
        await retriv_service.initialize()
        await retriv_service.index_documents(mixed_docs)
        
        # Search with project filter
        results = await retriv_service.search(
            "character",
            project_id="aladdin_movie",
            top_k=10
        )
        
        # All results should be from aladdin_movie
        for result in results:
            assert result["metadata"]["project_id"] == "aladdin_movie"
    
    @pytest.mark.asyncio
    async def test_custom_filters(self, retriv_service, aladdin_documents):
        """Test custom metadata filters."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Filter by type
        results = await retriv_service.search(
            "Aladdin",
            filters={"type": "scene"},
            top_k=10
        )
        
        # All results should be scenes
        for result in results:
            assert result["metadata"]["type"] == "scene"
    
    @pytest.mark.asyncio
    async def test_multiple_filters(self, retriv_service, aladdin_documents):
        """Test multiple filters combined."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        # Filter by type and category
        results = await retriv_service.search(
            "character",
            filters={"type": "character", "category": "protagonist"},
            top_k=10
        )
        
        # Should only get protagonist characters
        for result in results:
            assert result["metadata"]["type"] == "character"
            assert result["metadata"]["category"] == "protagonist"


class TestRetrivDocumentManagement:
    """Test document management operations."""
    
    @pytest.mark.asyncio
    async def test_update_document(self, retriv_service, aladdin_documents):
        """Test updating an existing document."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents[:2])
        
        # Update Aladdin's description
        updated_doc = {
            "id": "char_aladdin",
            "text": "Aladdin now wears a prince outfit with white and gold colors",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Aladdin",
                "category": "protagonist"
            }
        }
        
        await retriv_service.index_documents([updated_doc])
        
        # Search should find updated version
        results = await retriv_service.search("prince outfit white gold", top_k=3)
        
        assert len(results) > 0
        assert results[0]["id"] == "char_aladdin"
    
    @pytest.mark.asyncio
    async def test_delete_document(self, retriv_service, aladdin_documents):
        """Test deleting a document."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        initial_count = len(retriv_service._documents)
        
        # Delete a document
        await retriv_service.delete_document("char_jafar")
        
        # Verify document count decreased
        assert len(retriv_service._documents) == initial_count - 1
        
        # Search should not find deleted document
        results = await retriv_service.search("Jafar evil vizier", top_k=10)
        result_ids = [r["id"] for r in results]
        assert "char_jafar" not in result_ids
    
    @pytest.mark.asyncio
    async def test_clear_project(self, retriv_service, aladdin_documents):
        """Test clearing all documents for a project."""
        # Add documents from multiple projects
        mixed_docs = aladdin_documents + [
            {
                "id": "other_char",
                "text": "Character from different movie",
                "metadata": {"project_id": "other_movie", "type": "character"}
            }
        ]
        
        await retriv_service.initialize()
        await retriv_service.index_documents(mixed_docs)
        
        # Clear aladdin_movie project
        await retriv_service.clear_project("aladdin_movie")
        
        # Only other_movie documents should remain
        remaining = retriv_service._documents
        assert all(d["metadata"]["project_id"] != "aladdin_movie" for d in remaining)
        assert any(d["metadata"]["project_id"] == "other_movie" for d in remaining)


class TestRetrivStats:
    """Test statistics and monitoring."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, retriv_service, aladdin_documents):
        """Test getting index statistics."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        stats = retriv_service.get_stats()
        
        assert stats["initialized"] is True
        assert stats["total_documents"] == len(aladdin_documents)
        assert "index_path" in stats
        assert stats["index_path"] == retriv_service.index_path


class TestRetrivEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_search_empty_index(self, retriv_service):
        """Test searching an empty index."""
        await retriv_service.initialize()
        
        results = await retriv_service.search("test query", top_k=5)
        
        # Should return empty list, not error
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, retriv_service, aladdin_documents):
        """Test searching with empty query."""
        await retriv_service.initialize()
        await retriv_service.index_documents(aladdin_documents)
        
        results = await retriv_service.search("", top_k=5)
        
        # Should handle gracefully
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_index_empty_documents(self, retriv_service):
        """Test indexing empty document list."""
        await retriv_service.initialize()
        
        # Should not raise error
        await retriv_service.index_documents([])
        
        assert retriv_service._documents == []

