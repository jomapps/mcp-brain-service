"""Unit tests for Retriv service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.retriv_service import RetrivService, get_retriv_service


@pytest.fixture
def retriv_service():
    """Create a fresh RetrivService instance for testing."""
    return RetrivService(index_path="./test_data/retriv_index")


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "char_1",
            "text": "Aladdin wears a brown vest and purple pants",
            "metadata": {
                "project_id": "proj_1",
                "type": "character",
                "name": "Aladdin"
            }
        },
        {
            "id": "char_2",
            "text": "Jasmine wears a blue outfit with gold jewelry",
            "metadata": {
                "project_id": "proj_1",
                "type": "character",
                "name": "Jasmine"
            }
        },
        {
            "id": "scene_1",
            "text": "Scene 3: Aladdin meets Jasmine in the marketplace",
            "metadata": {
                "project_id": "proj_1",
                "type": "scene",
                "scene_number": 3
            }
        },
        {
            "id": "char_3",
            "text": "Genie is a blue magical being with incredible powers",
            "metadata": {
                "project_id": "proj_2",
                "type": "character",
                "name": "Genie"
            }
        }
    ]


class TestRetrivServiceInitialization:
    """Test Retriv service initialization."""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, retriv_service):
        """Test successful initialization."""
        with patch('retriv.HybridRetriever') as mock_retriever:
            mock_retriever.return_value = Mock()

            await retriv_service.initialize()

            assert retriv_service._initialized is True
            assert retriv_service.retriever is not None
            mock_retriever.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_import_error(self, retriv_service):
        """Test initialization with missing retriv package."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'retriv'")):
            await retriv_service.initialize()

            assert retriv_service._initialized is False
            assert retriv_service.retriever is None

    @pytest.mark.asyncio
    async def test_initialize_only_once(self, retriv_service):
        """Test that initialization only happens once."""
        with patch('retriv.HybridRetriever') as mock_retriever:
            mock_retriever.return_value = Mock()

            await retriv_service.initialize()
            await retriv_service.initialize()  # Second call

            # Should only be called once
            assert mock_retriever.call_count == 1


class TestRetrivServiceIndexing:
    """Test document indexing."""
    
    @pytest.mark.asyncio
    async def test_index_documents(self, retriv_service, sample_documents):
        """Test indexing documents."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            # Verify index was called
            mock_retriever.index.assert_called_once()

            # Verify documents are stored in memory
            assert len(retriv_service._documents) == len(sample_documents)

    @pytest.mark.asyncio
    async def test_index_documents_update_existing(self, retriv_service):
        """Test updating existing documents."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()

            # Index initial document
            doc1 = {"id": "doc_1", "text": "Original text", "metadata": {}}
            await retriv_service.index_documents([doc1])

            # Update same document
            doc1_updated = {"id": "doc_1", "text": "Updated text", "metadata": {}}
            await retriv_service.index_documents([doc1_updated])

            # Should have only one document
            assert len(retriv_service._documents) == 1
            assert retriv_service._documents[0]["text"] == "Updated text"

    @pytest.mark.asyncio
    async def test_index_documents_not_initialized(self, retriv_service, sample_documents):
        """Test indexing when service is not initialized."""
        with patch('builtins.__import__', side_effect=ImportError()):
            await retriv_service.index_documents(sample_documents)

            # Should not raise error, just log warning
            assert retriv_service._initialized is False


class TestRetrivServiceSearch:
    """Test search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_basic(self, retriv_service, sample_documents):
        """Test basic search."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever.search = Mock(return_value=[
                {"id": "char_1", "text": "Aladdin wears a brown vest", "score": 0.95, "metadata": {"project_id": "proj_1"}},
                {"id": "scene_1", "text": "Scene 3: Aladdin meets Jasmine", "score": 0.85, "metadata": {"project_id": "proj_1"}}
            ])
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            results = await retriv_service.search("brown vest", top_k=5)

            assert len(results) == 2
            assert results[0]["id"] == "char_1"
            mock_retriever.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_project_filter(self, retriv_service, sample_documents):
        """Test search with project_id filter."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever.search = Mock(return_value=[
                {"id": "char_1", "text": "Aladdin", "score": 0.95, "metadata": {"project_id": "proj_1"}},
                {"id": "char_3", "text": "Genie", "score": 0.90, "metadata": {"project_id": "proj_2"}}
            ])
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            results = await retriv_service.search("character", project_id="proj_1", top_k=5)

            # Should only return proj_1 results
            assert len(results) == 1
            assert results[0]["metadata"]["project_id"] == "proj_1"

    @pytest.mark.asyncio
    async def test_search_with_custom_filters(self, retriv_service, sample_documents):
        """Test search with custom metadata filters."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever.search = Mock(return_value=[
                {"id": "char_1", "text": "Aladdin", "score": 0.95, "metadata": {"project_id": "proj_1", "type": "character"}},
                {"id": "scene_1", "text": "Scene", "score": 0.90, "metadata": {"project_id": "proj_1", "type": "scene"}}
            ])
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            results = await retriv_service.search(
                "Aladdin",
                filters={"type": "character"},
                top_k=5
            )

            # Should only return character type
            assert len(results) == 1
            assert results[0]["metadata"]["type"] == "character"

    @pytest.mark.asyncio
    async def test_search_not_initialized(self, retriv_service):
        """Test search when service is not initialized."""
        with patch('builtins.__import__', side_effect=ImportError()):
            results = await retriv_service.search("test query")

            # Should return empty list, not raise error
            assert results == []


class TestRetrivServiceDeletion:
    """Test document deletion."""
    
    @pytest.mark.asyncio
    async def test_delete_document(self, retriv_service, sample_documents):
        """Test deleting a document."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            initial_count = len(retriv_service._documents)

            await retriv_service.delete_document("char_1")

            # Verify document removed from cache
            assert len(retriv_service._documents) == initial_count - 1
            assert not any(d["id"] == "char_1" for d in retriv_service._documents)

    @pytest.mark.asyncio
    async def test_clear_project(self, retriv_service, sample_documents):
        """Test clearing all documents for a project."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            await retriv_service.clear_project("proj_1")

            # Verify only proj_2 documents remain
            remaining_docs = retriv_service._documents
            assert all(d.get("metadata", {}).get("project_id") != "proj_1" for d in remaining_docs)
            assert any(d.get("metadata", {}).get("project_id") == "proj_2" for d in remaining_docs)


class TestRetrivServiceStats:
    """Test statistics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, retriv_service, sample_documents):
        """Test getting index statistics."""
        with patch('retriv.HybridRetriever') as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.index = Mock()
            mock_retriever_class.return_value = mock_retriever

            await retriv_service.initialize()
            await retriv_service.index_documents(sample_documents)

            stats = retriv_service.get_stats()

            assert stats["initialized"] is True
            assert stats["total_documents"] == len(sample_documents)
            assert "index_path" in stats


class TestRetrivServiceSingleton:
    """Test singleton pattern."""
    
    def test_get_retriv_service_singleton(self):
        """Test that get_retriv_service returns same instance."""
        service1 = get_retriv_service()
        service2 = get_retriv_service()
        
        assert service1 is service2

