"""
Gather Service for Brain Service
Handles batch operations, duplicate search, context retrieval, and coverage analysis
"""

import asyncio
import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.lib.embeddings import JinaEmbeddingService
from src.lib.neo4j_client import Neo4jClient
from src.lib.llm_client import OpenRouterClient
from src.models.batch import (
    BatchNodeInput, BatchNodeOutput,
    DuplicateResult, DepartmentNode, DepartmentContextData,
    RelevantNode, CoverageGatherItem, CoveredAspect, CoverageGap,
    CoverageAnalysis, QualityMetrics
)

logger = logging.getLogger(__name__)


class GatherService:
    """Service for gather-related operations"""
    
    def __init__(
        self,
        jina_service: JinaEmbeddingService,
        neo4j_client: Neo4jClient,
        llm_client: OpenRouterClient
    ):
        self.jina = jina_service
        self.neo4j = neo4j_client
        self.llm = llm_client
    
    async def batch_create_nodes(
        self,
        nodes: List[BatchNodeInput]
    ) -> Dict[str, Any]:
        """
        Create multiple nodes in a single batch operation
        
        Args:
            nodes: List of node inputs to create
            
        Returns:
            Dict with created nodes, IDs, and timing info
        """
        start_time = time.time()
        
        # Generate embeddings for all nodes in parallel
        embedding_start = time.time()
        contents = [node.content for node in nodes]
        embeddings = await self.jina.embed_batch(contents)
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Create nodes in Neo4j
        neo4j_start = time.time()
        created_nodes = []
        node_ids = []
        
        for i, (node_input, embedding) in enumerate(zip(nodes, embeddings)):
            try:
                # Generate unique ID
                node_id = str(uuid.uuid4())
                
                # Prepare node properties
                properties = {
                    "id": node_id,
                    "type": node_input.type,
                    "content": node_input.content,
                    "projectId": node_input.projectId,
                    "embedding": embedding,
                    "created_at": datetime.utcnow().isoformat(),
                    **node_input.properties
                }
                
                # Create node in Neo4j
                await self.neo4j.create_node(
                    labels=[node_input.type, "GatherItem"],
                    properties=properties
                )
                
                node_ids.append(node_id)
                created_nodes.append(BatchNodeOutput(
                    id=node_id,
                    type=node_input.type,
                    properties=node_input.properties,
                    embedding={
                        "dimensions": len(embedding),
                        "model": self.jina.model
                    }
                ))
                
            except Exception as e:
                logger.error(f"Failed to create node {i}: {e}")
                raise
        
        neo4j_time = (time.time() - neo4j_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "created": len(created_nodes),
            "nodeIds": node_ids,
            "nodes": created_nodes,
            "timing": {
                "embedding_time_ms": embedding_time,
                "neo4j_write_time_ms": neo4j_time,
                "total_time_ms": total_time
            }
        }
    
    async def search_duplicates(
        self,
        content: str,
        project_id: str,
        threshold: float = 0.90,
        limit: int = 10,
        node_type: Optional[str] = None,
        department: Optional[str] = None,
        exclude_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for semantically similar nodes (duplicates)
        
        Args:
            content: Text content to check for duplicates
            project_id: Project ID for isolation
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum results to return
            node_type: Filter by node type
            department: Filter by department
            exclude_node_ids: Node IDs to exclude from search
            
        Returns:
            Dict with duplicate results and timing info
        """
        start_time = time.time()
        
        # Generate embedding for query content
        embedding_start = time.time()
        query_embedding = await self.jina.embed_single(content)
        query_embedding_time = (time.time() - embedding_start) * 1000
        
        # Search for similar nodes in Neo4j
        search_start = time.time()
        
        # Build Cypher query with filters
        exclude_clause = ""
        if exclude_node_ids:
            exclude_clause = "AND NOT n.id IN $exclude_ids"
        
        type_clause = ""
        if node_type:
            type_clause = f"AND n.type = $node_type"
        
        dept_clause = ""
        if department:
            dept_clause = "AND n.department = $department"
        
        query = f"""
        MATCH (n:GatherItem {{projectId: $project_id}})
        WHERE n.embedding IS NOT NULL
        {type_clause}
        {dept_clause}
        {exclude_clause}
        WITH n, gds.similarity.cosine(n.embedding, $embedding) as similarity
        WHERE similarity >= $threshold
        RETURN n.id as nodeId, similarity, n.content as content, properties(n) as properties
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        params = {
            "project_id": project_id,
            "embedding": query_embedding,
            "threshold": threshold,
            "limit": limit
        }
        
        if node_type:
            params["node_type"] = node_type
        if department:
            params["department"] = department
        if exclude_node_ids:
            params["exclude_ids"] = exclude_node_ids
        
        results = await self.neo4j.run_query(query, params)
        
        duplicates = [
            DuplicateResult(
                nodeId=record["nodeId"],
                similarity=record["similarity"],
                content=record["content"],
                properties=record["properties"]
            )
            for record in results
        ]
        
        search_time = (time.time() - search_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        return {
            "duplicates": duplicates,
            "query_embedding_time_ms": query_embedding_time,
            "search_time_ms": search_time,
            "total_time_ms": total_time
        }
    
    async def get_department_context(
        self,
        project_id: str,
        target_department: str,
        previous_departments: List[str],
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Retrieve and aggregate context from previous departments
        
        Args:
            project_id: Project ID
            target_department: Target department slug
            previous_departments: List of previous department slugs
            limit: Nodes per department
            
        Returns:
            Dict with aggregated context and timing info
        """
        start_time = time.time()
        query_start = time.time()
        
        context = {}
        all_relevant_nodes = []
        total_nodes = 0
        
        # Query nodes from each previous department
        for dept in previous_departments:
            query = """
            MATCH (n:GatherItem {projectId: $project_id, department: $department})
            WHERE n.embedding IS NOT NULL
            RETURN n.id as nodeId, n.content as content, n.summary as summary,
                   n.qualityScore as qualityScore, n.embedding as embedding
            ORDER BY n.created_at DESC
            LIMIT $limit
            """
            
            results = await self.neo4j.run_query(query, {
                "project_id": project_id,
                "department": dept,
                "limit": limit
            })
            
            if not results:
                continue
            
            # Extract key themes using LLM
            contents = [r["content"] for r in results if r.get("content")]
            themes = await self.llm.extract_themes(contents, dept, max_themes=5)
            
            # Calculate average quality score
            quality_scores = [r.get("qualityScore", 0) for r in results if r.get("qualityScore")]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Prepare top nodes
            top_nodes = [
                DepartmentNode(
                    nodeId=r["nodeId"],
                    content=r["content"],
                    summary=r.get("summary"),
                    relevance=0.85  # Placeholder - could calculate based on embeddings
                )
                for r in results[:5]  # Top 5 nodes
            ]
            
            context[dept] = DepartmentContextData(
                nodeCount=len(results),
                qualityScore=avg_quality,
                topNodes=top_nodes,
                keyThemes=themes
            )
            
            # Add to relevant nodes
            for r in results:
                all_relevant_nodes.append(RelevantNode(
                    nodeId=r["nodeId"],
                    department=dept,
                    content=r["content"],
                    relevanceToTarget=0.80  # Placeholder
                ))
            
            total_nodes += len(results)
        
        query_time = (time.time() - query_start) * 1000
        
        # Generate aggregated summary
        aggregation_start = time.time()
        all_contents = [node.content for node in all_relevant_nodes[:15]]
        aggregated_summary = await self.llm.generate_summary(
            all_contents,
            context=f"Context for {target_department} department"
        )
        aggregation_time = (time.time() - aggregation_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "projectId": project_id,
            "targetDepartment": target_department,
            "context": context,
            "aggregatedSummary": aggregated_summary,
            "relevantNodes": all_relevant_nodes[:20],  # Limit to top 20
            "totalNodesAggregated": total_nodes,
            "timing": {
                "query_time_ms": query_time,
                "aggregation_time_ms": aggregation_time,
                "total_time_ms": total_time
            }
        }

    async def analyze_coverage(
        self,
        project_id: str,
        department: str,
        gather_items: List[CoverageGatherItem],
        department_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze content coverage and identify gaps

        Args:
            project_id: Project ID
            department: Department slug
            gather_items: List of gather items to analyze
            department_description: Optional department scope description

        Returns:
            Dict with coverage analysis and timing info
        """
        start_time = time.time()

        # Generate embeddings for gather items
        embedding_start = time.time()
        contents = [item.content for item in gather_items]
        embeddings = await self.jina.embed_batch(contents)
        embedding_time = (time.time() - embedding_start) * 1000

        # Use LLM to analyze coverage
        analysis_start = time.time()

        # Prepare items for LLM
        items_for_analysis = [
            {
                "content": item.content,
                "summary": item.summary or ""
            }
            for item in gather_items
        ]

        # Get coverage analysis from LLM
        llm_analysis = await self.llm.analyze_coverage(
            items_for_analysis,
            department,
            department_description or f"{department} department"
        )

        # Parse LLM response into structured format with validation
        covered_aspects = []
        for aspect in llm_analysis.get("coveredAspects", []):
            try:
                # Ensure all required fields are present
                if "aspect" in aspect and "coverage" in aspect and "itemCount" in aspect and "quality" in aspect:
                    covered_aspects.append(CoveredAspect(**aspect))
            except Exception as e:
                logger.warning(f"Failed to parse covered aspect: {e}")

        gaps = []
        for gap in llm_analysis.get("gaps", []):
            try:
                # Ensure all required fields are present, provide defaults if missing
                gap_data = {
                    "aspect": gap.get("aspect", "Unknown"),
                    "coverage": gap.get("coverage", 0),
                    "itemCount": gap.get("itemCount", 0),
                    "severity": gap.get("severity", "medium"),
                    "suggestion": gap.get("suggestion", "No suggestion provided")
                }
                gaps.append(CoverageGap(**gap_data))
            except Exception as e:
                logger.warning(f"Failed to parse gap: {e}")

        recommendations = llm_analysis.get("recommendations", [])

        # Calculate overall coverage score
        if covered_aspects:
            coverage_score = int(sum(a.coverage for a in covered_aspects) / len(covered_aspects))
        else:
            coverage_score = 0

        # Calculate item distribution (simple clustering by keywords)
        item_distribution = self._calculate_item_distribution(gather_items, department)

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(
            gather_items,
            covered_aspects,
            gaps
        )

        analysis_time = (time.time() - analysis_start) * 1000
        total_time = (time.time() - start_time) * 1000

        return {
            "department": department,
            "coverageScore": coverage_score,
            "analysis": CoverageAnalysis(
                coveredAspects=covered_aspects,
                gaps=gaps,
                recommendations=recommendations
            ),
            "itemDistribution": item_distribution,
            "qualityMetrics": quality_metrics,
            "timing": {
                "embedding_time_ms": embedding_time,
                "analysis_time_ms": analysis_time,
                "total_time_ms": total_time
            }
        }

    def _calculate_item_distribution(
        self,
        gather_items: List[CoverageGatherItem],
        department: str
    ) -> Dict[str, int]:
        """Calculate distribution of items by topic/aspect"""
        # Simple keyword-based distribution
        # In production, this could use clustering or LLM classification
        distribution = {}

        # Define common keywords for different aspects
        aspect_keywords = {
            "plot": ["plot", "story", "narrative", "arc"],
            "character": ["character", "protagonist", "personality"],
            "theme": ["theme", "message", "meaning"],
            "pacing": ["pacing", "tempo", "rhythm", "timing"],
            "dialogue": ["dialogue", "conversation", "speech"],
            "visual": ["visual", "aesthetic", "style", "look"],
            "setting": ["setting", "location", "environment", "world"]
        }

        for item in gather_items:
            content_lower = item.content.lower()
            summary_lower = (item.summary or "").lower()
            combined = content_lower + " " + summary_lower

            for aspect, keywords in aspect_keywords.items():
                if any(keyword in combined for keyword in keywords):
                    distribution[aspect] = distribution.get(aspect, 0) + 1

        return distribution

    def _calculate_quality_metrics(
        self,
        gather_items: List[CoverageGatherItem],
        covered_aspects: List[CoveredAspect],
        gaps: List[CoverageGap]
    ) -> QualityMetrics:
        """Calculate quality metrics for coverage"""
        # Depth: Average coverage of covered aspects
        if covered_aspects:
            depth = int(sum(a.coverage for a in covered_aspects) / len(covered_aspects))
        else:
            depth = 0

        # Breadth: Ratio of covered aspects to total expected aspects
        total_aspects = len(covered_aspects) + len(gaps)
        if total_aspects > 0:
            breadth = int((len(covered_aspects) / total_aspects) * 100)
        else:
            breadth = 50

        # Coherence: Based on quality ratings of covered aspects
        quality_scores = {"excellent": 100, "good": 75, "fair": 50, "poor": 25}
        if covered_aspects:
            coherence = int(
                sum(quality_scores.get(a.quality, 50) for a in covered_aspects) / len(covered_aspects)
            )
        else:
            coherence = 50

        # Actionability: Based on number of items and specificity
        avg_content_length = sum(len(item.content) for item in gather_items) / len(gather_items)
        actionability = min(100, int((avg_content_length / 500) * 100))  # 500 chars = good detail

        return QualityMetrics(
            depth=depth,
            breadth=breadth,
            coherence=coherence,
            actionability=actionability
        )

