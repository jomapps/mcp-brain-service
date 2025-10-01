"""Retriv hybrid search service for enhanced querying."""

from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class RetrivService:
    """Wrapper around Retriv for hybrid search (BM25 + embeddings)."""
    
    def __init__(self, index_path: str = "./data/retriv_index"):
        self.index_path = index_path
        self.retriever = None
        self._initialized = False
        self._documents = []  # In-memory cache for re-indexing
    
    async def initialize(self):
        """Initialize Retriv retriever."""
        if self._initialized:
            return
        
        try:
            # Import here to avoid issues if retriv not installed
            from retriv import HybridRetriever
            
            # Ensure index directory exists
            Path(self.index_path).mkdir(parents=True, exist_ok=True)
            
            self.retriever = HybridRetriever(
                index_name="brain_service",
                sr_model="bm25",  # Sparse retrieval model (BM25)
                dr_model="sentence-transformers/all-MiniLM-L6-v2",  # Dense retrieval model (embeddings)
                min_df=1,
                tokenizer="whitespace",
                stemmer="english",
                stopwords="english",
                do_lowercasing=True,
                do_ampersand_normalization=True,
                do_special_chars_normalization=True,
                do_acronyms_normalization=True,
                do_punctuation_removal=True,
                normalize=True,
                max_length=128,
                use_ann=True,
            )
            self._initialized = True
            logger.info("Retriv service initialized successfully")
        except ImportError as e:
            logger.warning(f"Retriv not available: {e}. Hybrid search will be disabled.")
            self._initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize Retriv: {e}")
            raise
    
    async def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for hybrid search.
        
        Args:
            documents: List of documents with structure:
                {
                    "id": "unique_id",
                    "text": "searchable text content",
                    "metadata": {...}
                }
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.retriever:
            logger.warning("Retriv not initialized, skipping indexing")
            return
        
        # Store documents in memory for potential re-indexing
        for doc in documents:
            # Update or append document
            existing_idx = next(
                (i for i, d in enumerate(self._documents) if d["id"] == doc["id"]),
                None
            )
            if existing_idx is not None:
                self._documents[existing_idx] = doc
            else:
                self._documents.append(doc)
        
        # Prepare documents for Retriv
        collection = [
            {
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc.get("metadata", {})
            }
            for doc in self._documents
        ]
        
        try:
            # Index documents
            self.retriever.index(collection)
            logger.info(f"Indexed {len(collection)} documents in Retriv")
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search using BM25 + embeddings.
        
        Args:
            query: Search query
            top_k: Number of results to return
            project_id: Filter by project ID
            filters: Additional metadata filters
        
        Returns:
            List of search results with scores
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.retriever:
            logger.warning("Retriv not initialized, returning empty results")
            return []
        
        try:
            # Perform hybrid search
            results = self.retriever.search(
                query=query,
                return_docs=True,
                cutoff=top_k * 2  # Get more results for filtering
            )
            
            # Apply filters
            filtered_results = []
            for result in results:
                metadata = result.get("metadata", {})
                
                # Filter by project_id
                if project_id and metadata.get("project_id") != project_id:
                    continue
                
                # Apply custom filters
                if filters:
                    if not self._matches_filters(metadata, filters):
                        continue
                
                filtered_results.append(result)
            
            return filtered_results[:top_k]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                # Check if any filter value matches
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True
    
    async def delete_document(self, doc_id: str):
        """Delete a document from the index."""
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.retriever:
            logger.warning("Retriv not initialized, skipping deletion")
            return
        
        # Remove from in-memory cache
        self._documents = [d for d in self._documents if d["id"] != doc_id]
        
        # Re-index remaining documents
        if self._documents:
            await self.index_documents([])  # Triggers re-index with current documents
        
        logger.info(f"Deleted document {doc_id} from Retriv index")
    
    async def clear_project(self, project_id: str):
        """Clear all documents for a project."""
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.retriever:
            logger.warning("Retriv not initialized, skipping project clear")
            return
        
        # Remove project documents from cache
        self._documents = [
            d for d in self._documents 
            if d.get("metadata", {}).get("project_id") != project_id
        ]
        
        # Re-index remaining documents
        if self._documents:
            await self.index_documents([])  # Triggers re-index with current documents
        
        logger.info(f"Cleared project {project_id} from Retriv index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        return {
            "initialized": self._initialized,
            "total_documents": len(self._documents),
            "index_path": self.index_path
        }


# Global instance
_retriv_service: Optional[RetrivService] = None


def get_retriv_service() -> RetrivService:
    """Get or create global Retriv service instance."""
    global _retriv_service
    
    if _retriv_service is None:
        _retriv_service = RetrivService()
    
    return _retriv_service

