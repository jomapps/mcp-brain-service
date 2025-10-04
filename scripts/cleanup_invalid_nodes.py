#!/usr/bin/env python3
"""
Cleanup Invalid Nodes Script

This script removes invalid/irrelevant nodes from the Neo4j knowledge graph.
It targets nodes with error messages, empty content, or other invalid patterns.

Usage:
    # Clean all projects
    python scripts/cleanup_invalid_nodes.py
    
    # Clean specific project
    python scripts/cleanup_invalid_nodes.py --project-id my-project-123
    
    # Dry run (preview what would be deleted)
    python scripts/cleanup_invalid_nodes.py --dry-run
    
    # Custom patterns
    python scripts/cleanup_invalid_nodes.py --patterns "Error:" "undefined" "null"
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lib.neo4j_client import get_neo4j_client, Neo4jClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Default invalid patterns to search for
DEFAULT_INVALID_PATTERNS = [
    "Error:",
    "error:",
    "no user message",
    "No user message",
    "undefined",
    "null",
    "NULL",
    "[object Object]",
    "NaN",
]


async def find_invalid_nodes(
    neo4j_client: Neo4jClient,
    patterns: List[str],
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find nodes matching invalid patterns
    
    Args:
        neo4j_client: Neo4j client instance
        patterns: List of patterns to search for
        project_id: Optional project ID to filter by
        
    Returns:
        List of matching nodes with their details
    """
    all_matches = []
    
    for pattern in patterns:
        logger.info(f"Searching for nodes containing pattern: '{pattern}'")
        
        # Build query
        query = """
        MATCH (n:Document)
        WHERE n.content CONTAINS $pattern
        """
        
        if project_id:
            query += " AND n.project_id = $project_id"
        
        query += """
        RETURN n.id as id, n.content as content, n.project_id as project_id,
               n.document_type as type, n.created_at as created_at
        LIMIT 1000
        """
        
        params = {"pattern": pattern}
        if project_id:
            params["project_id"] = project_id
        
        try:
            results = await neo4j_client.run_query(query, params)
            
            if results:
                logger.info(f"  Found {len(results)} nodes matching '{pattern}'")
                all_matches.extend(results)
            else:
                logger.info(f"  No nodes found matching '{pattern}'")
                
        except Exception as e:
            logger.error(f"  Error searching for pattern '{pattern}': {e}")
    
    # Remove duplicates based on node ID
    unique_matches = {node['id']: node for node in all_matches}.values()
    return list(unique_matches)


async def delete_invalid_nodes(
    neo4j_client: Neo4jClient,
    patterns: List[str],
    project_id: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Delete nodes matching invalid patterns
    
    Args:
        neo4j_client: Neo4j client instance
        patterns: List of patterns to search for
        project_id: Optional project ID to filter by
        dry_run: If True, only preview deletions without executing
        
    Returns:
        Dictionary with deletion statistics
    """
    stats = {
        "total_found": 0,
        "total_deleted": 0,
        "by_pattern": {},
        "by_project": {},
        "errors": []
    }
    
    for pattern in patterns:
        logger.info(f"Processing pattern: '{pattern}'")
        
        # Build query
        if dry_run:
            query = """
            MATCH (n:Document)
            WHERE n.content CONTAINS $pattern
            """
            if project_id:
                query += " AND n.project_id = $project_id"
            query += """
            RETURN count(n) as count, collect(n.id)[0..5] as sample_ids
            """
        else:
            query = """
            MATCH (n:Document)
            WHERE n.content CONTAINS $pattern
            """
            if project_id:
                query += " AND n.project_id = $project_id"
            query += """
            WITH n
            DETACH DELETE n
            RETURN count(n) as count
            """
        
        params = {"pattern": pattern}
        if project_id:
            params["project_id"] = project_id
        
        try:
            results = await neo4j_client.run_query(query, params)
            
            if results:
                count = results[0].get("count", 0)
                stats["by_pattern"][pattern] = count
                
                if dry_run and count > 0:
                    sample_ids = results[0].get("sample_ids", [])
                    logger.info(f"  Would delete {count} nodes")
                    logger.info(f"  Sample IDs: {sample_ids}")
                elif count > 0:
                    logger.info(f"  Deleted {count} nodes")
                    stats["total_deleted"] += count
                else:
                    logger.info(f"  No nodes found")
                
                stats["total_found"] += count
                
        except Exception as e:
            error_msg = f"Error processing pattern '{pattern}': {e}"
            logger.error(f"  {error_msg}")
            stats["errors"].append(error_msg)
    
    return stats


async def get_project_stats(neo4j_client: Neo4jClient) -> Dict[str, int]:
    """Get node count by project"""
    query = """
    MATCH (n:Document)
    RETURN n.project_id as project_id, count(n) as count
    ORDER BY count DESC
    """
    
    try:
        results = await neo4j_client.run_query(query, {})
        return {r["project_id"]: r["count"] for r in results if r.get("project_id")}
    except Exception as e:
        logger.error(f"Failed to get project stats: {e}")
        return {}


async def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(
        description="Clean up invalid nodes from the knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--project-id",
        type=str,
        help="Filter by specific project ID"
    )
    
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=DEFAULT_INVALID_PATTERNS,
        help="Custom patterns to search for (default: common error patterns)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all projects and their node counts"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Connect to Neo4j
    logger.info("Connecting to Neo4j...")
    try:
        neo4j_client = await get_neo4j_client()
        logger.info("✅ Connected to Neo4j successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neo4j: {e}")
        logger.error("Please check your NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables")
        return 1
    
    # List projects if requested
    if args.list_projects:
        logger.info("\n" + "="*60)
        logger.info("PROJECT STATISTICS")
        logger.info("="*60)
        
        project_stats = await get_project_stats(neo4j_client)
        
        if project_stats:
            for project_id, count in project_stats.items():
                logger.info(f"  {project_id}: {count} nodes")
        else:
            logger.info("  No projects found")
        
        logger.info("="*60 + "\n")
        return 0
    
    # Run cleanup
    logger.info("\n" + "="*60)
    logger.info("CLEANUP INVALID NODES")
    logger.info("="*60)
    logger.info(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE DELETION'}")
    logger.info(f"Project filter: {args.project_id or 'All projects'}")
    logger.info(f"Patterns: {', '.join(args.patterns)}")
    logger.info("="*60 + "\n")
    
    if not args.dry_run:
        logger.warning("⚠️  This will permanently delete nodes from the database!")
        logger.warning("⚠️  Press Ctrl+C within 5 seconds to cancel...")
        await asyncio.sleep(5)
    
    # Execute cleanup
    start_time = datetime.now()
    
    stats = await delete_invalid_nodes(
        neo4j_client=neo4j_client,
        patterns=args.patterns,
        project_id=args.project_id,
        dry_run=args.dry_run
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("CLEANUP SUMMARY")
    logger.info("="*60)
    logger.info(f"Total nodes found: {stats['total_found']}")
    
    if args.dry_run:
        logger.info(f"Would delete: {stats['total_found']} nodes")
    else:
        logger.info(f"Total deleted: {stats['total_deleted']}")
    
    logger.info(f"\nBy pattern:")
    for pattern, count in stats['by_pattern'].items():
        logger.info(f"  '{pattern}': {count}")
    
    if stats['errors']:
        logger.info(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors']:
            logger.error(f"  {error}")
    
    logger.info(f"\nDuration: {duration:.2f} seconds")
    logger.info("="*60 + "\n")
    
    if args.dry_run:
        logger.info("✅ Dry run completed. Run without --dry-run to actually delete nodes.")
    else:
        logger.info("✅ Cleanup completed successfully!")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\n❌ Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)

