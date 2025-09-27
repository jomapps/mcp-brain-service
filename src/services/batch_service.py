import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from ..models.knowledge import Document, EmbeddingResult
from ..services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

class BatchService:
    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service
        self.batch_size = 50  # Process in batches of 50
        self.max_concurrent = 5  # Max concurrent batch operations
    
    async def process_document_batch(self, documents: List[Document], project_id: str) -> Dict[str, Any]:
        """Process large batches of documents efficiently"""
        start_time = datetime.utcnow()
        total_documents = len(documents)
        processed_count = 0
        failed_count = 0
        document_ids = []
        
        try:
            # Split into smaller batches
            batches = [documents[i:i + self.batch_size] for i in range(0, len(documents), self.batch_size)]
            
            # Process batches with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_batch(batch: List[Document]) -> List[str]:
                async with semaphore:
                    try:
                        batch_ids = await self.knowledge_service.bulk_store_documents(batch, project_id)
                        nonlocal processed_count
                        processed_count += len(batch_ids)
                        logger.info(f"Processed batch of {len(batch_ids)} documents")
                        return batch_ids
                    except Exception as e:
                        nonlocal failed_count
                        failed_count += len(batch)
                        logger.error(f"Failed to process batch: {str(e)}")
                        return []
            
            # Execute all batches concurrently
            batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches], return_exceptions=True)
            
            # Collect results
            for result in batch_results:
                if isinstance(result, list):
                    document_ids.extend(result)
                else:
                    logger.error(f"Batch processing error: {result}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "batch_id": str(uuid.uuid4()),
                "total_documents": total_documents,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "document_ids": document_ids,
                "processing_time_seconds": processing_time,
                "documents_per_second": processed_count / processing_time if processing_time > 0 else 0,
                "success_rate": processed_count / total_documents if total_documents > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise Exception(f"Batch processing failed: {str(e)}")
    
    async def batch_similarity_search(self, queries: List[str], project_id: str, limit_per_query: int = 10) -> Dict[str, Any]:
        """Perform batch similarity searches"""
        start_time = datetime.utcnow()
        
        try:
            # Generate embeddings for all queries
            query_embeddings = await self.knowledge_service.jina.embed_batch(queries)
            
            # Perform searches concurrently
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def search_single(query_embedding: List[float], query_index: int):
                async with semaphore:
                    try:
                        return await self.knowledge_service.search_by_embedding(
                            query_embedding, project_id, limit_per_query
                        )
                    except Exception as e:
                        logger.error(f"Search failed for query {query_index}: {str(e)}")
                        return None
            
            search_results = await asyncio.gather(*[
                search_single(embedding, i) 
                for i, embedding in enumerate(query_embeddings)
            ], return_exceptions=True)
            
            # Process results
            successful_searches = []
            failed_searches = 0
            
            for i, result in enumerate(search_results):
                if result and not isinstance(result, Exception):
                    successful_searches.append({
                        "query_index": i,
                        "query": queries[i],
                        "results": result
                    })
                else:
                    failed_searches += 1
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "batch_id": str(uuid.uuid4()),
                "total_queries": len(queries),
                "successful_searches": len(successful_searches),
                "failed_searches": failed_searches,
                "results": successful_searches,
                "processing_time_seconds": processing_time,
                "queries_per_second": len(queries) / processing_time if processing_time > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Batch similarity search failed: {str(e)}")
            raise Exception(f"Batch similarity search failed: {str(e)}")
    
    async def batch_relationship_creation(self, relationships: List[Dict[str, Any]], project_id: str) -> Dict[str, Any]:
        """Create multiple relationships in batch"""
        start_time = datetime.utcnow()
        created_count = 0
        failed_count = 0
        
        try:
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def create_relationship(rel_data: Dict[str, Any]):
                async with semaphore:
                    try:
                        success = await self.knowledge_service.create_relationship(
                            from_id=rel_data["from_id"],
                            to_id=rel_data["to_id"],
                            relationship_type=rel_data["type"],
                            properties=rel_data.get("properties", {})
                        )
                        nonlocal created_count, failed_count
                        if success:
                            created_count += 1
                        else:
                            failed_count += 1
                        return success
                    except Exception as e:
                        logger.error(f"Failed to create relationship: {str(e)}")
                        failed_count += 1
                        return False
            
            # Execute all relationship creations concurrently
            results = await asyncio.gather(*[
                create_relationship(rel) for rel in relationships
            ], return_exceptions=True)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "batch_id": str(uuid.uuid4()),
                "total_relationships": len(relationships),
                "created_count": created_count,
                "failed_count": failed_count,
                "processing_time_seconds": processing_time,
                "relationships_per_second": len(relationships) / processing_time if processing_time > 0 else 0,
                "success_rate": created_count / len(relationships) if relationships else 0
            }
            
        except Exception as e:
            logger.error(f"Batch relationship creation failed: {str(e)}")
            raise Exception(f"Batch relationship creation failed: {str(e)}")
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get status of a batch operation (placeholder for future implementation)"""
        # In a production system, you'd store batch status in Redis or database
        return {
            "batch_id": batch_id,
            "status": "completed",  # "pending", "processing", "completed", "failed"
            "message": "Batch operation completed successfully"
        }