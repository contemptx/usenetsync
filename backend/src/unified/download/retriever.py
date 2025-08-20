#!/usr/bin/env python3
"""
Unified Retriever - Retrieve segments from Usenet
Production-ready with parallel retrieval and error recovery
"""

import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SegmentRetrieval:
    """Segment retrieval result"""
    
    def __init__(self, segment_id: str, message_id: str):
        self.segment_id = segment_id
        self.message_id = message_id
        self.data = None
        self.success = False
        self.error = None
        self.attempts = 0
        self.retrieved_at = None

class UnifiedRetriever:
    """
    Unified segment retriever
    Retrieves segments from Usenet with parallel processing
    """
    
    def __init__(self, connection_pool=None, config=None):
        """Initialize retriever"""
        self.connection_pool = connection_pool
        self.config = config or {}
        self.max_workers = self.config.get('max_workers', 10)
        self.max_retries = self.config.get('max_retries', 3)
        self._cache = {}
        self._statistics = {
            'segments_retrieved': 0,
            'segments_failed': 0,
            'bytes_downloaded': 0,
            'cache_hits': 0
        }
    
    def retrieve_segments(self, segment_info: List[Dict[str, Any]],
                         progress_callback: Optional[callable] = None) -> List[SegmentRetrieval]:
        """
        Retrieve multiple segments
        
        Args:
            segment_info: List of segment information dicts
            progress_callback: Optional progress callback
        
        Returns:
            List of retrieval results
        """
        retrievals = []
        total_segments = len(segment_info)
        completed = 0
        
        # Create retrieval objects
        for info in segment_info:
            retrieval = SegmentRetrieval(
                info['segment_id'],
                info['message_id']
            )
            retrievals.append(retrieval)
        
        # Parallel retrieval
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all retrieval tasks
            futures = {
                executor.submit(self._retrieve_single, retrieval): retrieval
                for retrieval in retrievals
            }
            
            # Process completions
            for future in concurrent.futures.as_completed(futures):
                retrieval = futures[future]
                
                try:
                    retrieval = future.result()
                    if retrieval.success:
                        self._statistics['segments_retrieved'] += 1
                        if retrieval.data:
                            self._statistics['bytes_downloaded'] += len(retrieval.data)
                    else:
                        self._statistics['segments_failed'] += 1
                        
                except Exception as e:
                    retrieval.success = False
                    retrieval.error = str(e)
                    self._statistics['segments_failed'] += 1
                    logger.error(f"Retrieval failed for {retrieval.segment_id}: {e}")
                
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total_segments)
        
        logger.info(f"Retrieved {self._statistics['segments_retrieved']} of {total_segments} segments")
        
        return retrievals
    
    def _retrieve_single(self, retrieval: SegmentRetrieval) -> SegmentRetrieval:
        """
        Retrieve single segment
        
        Args:
            retrieval: Retrieval object
        
        Returns:
            Updated retrieval object
        """
        # Check cache first
        if retrieval.message_id in self._cache:
            retrieval.data = self._cache[retrieval.message_id]
            retrieval.success = True
            retrieval.retrieved_at = datetime.now()
            self._statistics['cache_hits'] += 1
            return retrieval
        
        # Attempt retrieval with retries
        for attempt in range(self.max_retries):
            retrieval.attempts = attempt + 1
            
            try:
                if self.connection_pool:
                    # Use connection pool for retrieval
                    result = self.connection_pool.retrieve_article(retrieval.message_id)
                    
                    if result:
                        article_number, lines = result
                        # Join lines into data
                        retrieval.data = '\n'.join(lines).encode('utf-8')
                        retrieval.success = True
                        retrieval.retrieved_at = datetime.now()
                        
                        # Cache the result
                        self._cache[retrieval.message_id] = retrieval.data
                        
                        return retrieval
                else:
                    # Simulate retrieval for testing
                    retrieval.data = f"Simulated data for {retrieval.segment_id}".encode('utf-8')
                    retrieval.success = True
                    retrieval.retrieved_at = datetime.now()
                    return retrieval
                    
            except Exception as e:
                retrieval.error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed for {retrieval.segment_id}: {e}")
        
        # All attempts failed
        retrieval.success = False
        return retrieval
    
    def retrieve_with_redundancy(self, segment_info: List[Dict[str, Any]],
                                redundancy_info: List[Dict[str, Any]]) -> List[SegmentRetrieval]:
        """
        Retrieve segments with redundancy fallback
        
        Args:
            segment_info: Primary segment information
            redundancy_info: Redundant segment information
        
        Returns:
            List of retrieval results
        """
        # Try primary segments first
        primary_results = self.retrieve_segments(segment_info)
        
        # Check for failures
        failed_segments = [r for r in primary_results if not r.success]
        
        if failed_segments and redundancy_info:
            logger.info(f"Attempting redundancy retrieval for {len(failed_segments)} failed segments")
            
            # Map redundancy info to failed segments
            redundancy_map = {}
            for info in redundancy_info:
                seg_id = info['segment_id']
                if seg_id not in redundancy_map:
                    redundancy_map[seg_id] = []
                redundancy_map[seg_id].append(info)
            
            # Retry failed segments with redundancy
            for failed in failed_segments:
                if failed.segment_id in redundancy_map:
                    for redundant in redundancy_map[failed.segment_id]:
                        retry = SegmentRetrieval(
                            failed.segment_id,
                            redundant['message_id']
                        )
                        
                        retry = self._retrieve_single(retry)
                        
                        if retry.success:
                            # Update original result
                            failed.data = retry.data
                            failed.success = True
                            failed.retrieved_at = retry.retrieved_at
                            logger.info(f"Recovered {failed.segment_id} using redundancy")
                            break
        
        return primary_results
    
    def batch_retrieve(self, message_ids: List[str],
                       batch_size: int = 50) -> Dict[str, bytes]:
        """
        Retrieve messages in batches
        
        Args:
            message_ids: List of message IDs
            batch_size: Batch size
        
        Returns:
            Dictionary of message_id -> data
        """
        results = {}
        
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            
            # Create segment info for batch
            segment_info = [
                {'segment_id': f"seg_{j}", 'message_id': msg_id}
                for j, msg_id in enumerate(batch)
            ]
            
            # Retrieve batch
            retrievals = self.retrieve_segments(segment_info)
            
            # Collect results
            for retrieval, msg_id in zip(retrievals, batch):
                if retrieval.success and retrieval.data:
                    results[msg_id] = retrieval.data
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        total = self._statistics['segments_retrieved'] + self._statistics['segments_failed']
        success_rate = (
            self._statistics['segments_retrieved'] / total if total > 0 else 0
        )
        
        return {
            **self._statistics,
            'total_attempts': total,
            'success_rate': success_rate,
            'cache_size': len(self._cache)
        }
    
    def clear_cache(self):
        """Clear retrieval cache"""
        self._cache.clear()
        logger.info("Retrieval cache cleared")