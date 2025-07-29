#!/usr/bin/env python3
"""
Segment Retrieval System for UsenetSync
Implements intelligent retrieval hierarchy and fallback mechanisms
"""

import os
import time
import logging
import hashlib
import threading
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import heapq

logger = logging.getLogger(__name__)

class RetrievalMethod(Enum):
    """Retrieval methods in order of preference"""
    MESSAGE_ID = 1      # Direct message ID
    REDUNDANCY = 2      # Redundancy recovery
    SUBJECT_HASH = 3    # Subject-based search

@dataclass
class RetrievalAttempt:
    """Record of retrieval attempt"""
    method: RetrievalMethod
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    duration: float = 0.0
    bytes_retrieved: int = 0

@dataclass
class SegmentRequest:
    """Segment retrieval request"""
    segment_id: str
    file_path: str
    segment_index: int
    primary_message_id: Optional[str]
    subject_hash: Optional[str]
    newsgroup: str
    expected_hash: str
    expected_size: int
    redundancy_available: bool = False
    priority: int = 5
    attempts: List[RetrievalAttempt] = field(default_factory=list)
    
    def can_use_method(self, method: RetrievalMethod) -> bool:
        """Check if method can be used"""
        if method == RetrievalMethod.MESSAGE_ID:
            return self.primary_message_id is not None
        elif method == RetrievalMethod.SUBJECT_HASH:
            return self.subject_hash is not None
        elif method == RetrievalMethod.REDUNDANCY:
            return self.redundancy_available
        return True  # Other methods always available

class ServerHealthTracker:
    """Tracks server health for intelligent routing"""
    
    def __init__(self):
        self.server_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
    def record_attempt(self, server: str, success: bool, 
                      response_time: float, method: RetrievalMethod):
        """Record retrieval attempt"""
        with self._lock:
            if server not in self.server_stats:
                self.server_stats[server] = {
                    'total_attempts': 0,
                    'successful_attempts': 0,
                    'total_response_time': 0.0,
                    'last_success': None,
                    'last_failure': None,
                    'method_stats': {}
                }
                
            stats = self.server_stats[server]
            stats['total_attempts'] += 1
            
            if success:
                stats['successful_attempts'] += 1
                stats['total_response_time'] += response_time
                stats['last_success'] = datetime.now()
            else:
                stats['last_failure'] = datetime.now()
                
            # Track per-method stats
            method_name = method.name
            if method_name not in stats['method_stats']:
                stats['method_stats'][method_name] = {
                    'attempts': 0,
                    'successes': 0
                }
                
            stats['method_stats'][method_name]['attempts'] += 1
            if success:
                stats['method_stats'][method_name]['successes'] += 1
                
    def get_server_score(self, server: str, method: RetrievalMethod) -> float:
        """Get server score for method (higher is better)"""
        with self._lock:
            if server not in self.server_stats:
                return 0.5  # Neutral score for new servers
                
            stats = self.server_stats[server]
            
            # Overall success rate
            if stats['total_attempts'] == 0:
                overall_rate = 0.5
            else:
                overall_rate = stats['successful_attempts'] / stats['total_attempts']
                
            # Method-specific success rate
            method_stats = stats['method_stats'].get(method.name, {})
            if method_stats.get('attempts', 0) == 0:
                method_rate = overall_rate  # Use overall if no method data
            else:
                method_rate = method_stats['successes'] / method_stats['attempts']
                
            # Average response time factor
            if stats['successful_attempts'] > 0:
                avg_time = stats['total_response_time'] / stats['successful_attempts']
                time_factor = 1.0 / (1.0 + avg_time)  # Lower time = higher score
            else:
                time_factor = 0.5
                
            # Recency factor
            recency_factor = 1.0
            if stats['last_failure']:
                time_since_failure = (datetime.now() - stats['last_failure']).total_seconds()
                if time_since_failure < 300:  # Recent failure
                    recency_factor = 0.5
                    
            # Combined score
            return method_rate * time_factor * recency_factor * overall_rate
            
    def get_best_servers(self, method: RetrievalMethod, count: int = 3) -> List[str]:
        """Get best servers for method"""
        with self._lock:
            server_scores = [
                (self.get_server_score(server, method), server)
                for server in self.server_stats.keys()
            ]
            
            # Sort by score descending
            server_scores.sort(reverse=True)
            
            return [server for _, server in server_scores[:count]]

class RetrieverStrategy:
    """Base class for retrieval strategies"""
    
    def __init__(self, nntp_client):
        self.nntp = nntp_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def retrieve(self, request: SegmentRequest) -> Tuple[bool, Optional[bytes], str]:
        """
        Attempt to retrieve segment
        Returns: (success, data, error_message)
        """
        raise NotImplementedError

class MessageIDRetriever(RetrieverStrategy):
    """Direct message ID retrieval"""
    
    def retrieve(self, request: SegmentRequest) -> Tuple[bool, Optional[bytes], str]:
        """Retrieve by message ID"""
        if not request.primary_message_id:
            return False, None, "No message ID available"
            
        try:
            data = self.nntp.retrieve_article(
                request.primary_message_id,
                request.newsgroup
            )
            
            if data:
                # Verify hash
                actual_hash = hashlib.sha256(data).hexdigest()
                if actual_hash == request.expected_hash:
                    return True, data, ""
                else:
                    return False, None, f"Hash mismatch: {actual_hash}"
            else:
                return False, None, "Article not found"
                
        except Exception as e:
            return False, None, str(e)

class SubjectSearchRetriever(RetrieverStrategy):
    """Subject-based search retrieval"""
    
    def retrieve(self, request: SegmentRequest) -> Tuple[bool, Optional[bytes], str]:
        """Retrieve by subject search"""
        if not request.subject_hash:
            return False, None, "No subject hash available"
            
        try:
            # Search for articles with matching subject
            articles = self._search_by_subject(
                request.newsgroup,
                request.subject_hash
            )
            
            for article_id in articles:
                data = self.nntp.retrieve_article(article_id, request.newsgroup)
                
                if data:
                    # Verify hash
                    actual_hash = hashlib.sha256(data).hexdigest()
                    if actual_hash == request.expected_hash:
                        return True, data, ""
                        
            return False, None, "No matching articles found"
            
        except Exception as e:
            return False, None, str(e)
            
    def _search_by_subject(self, newsgroup: str, subject: str) -> List[str]:
        """Search for articles by subject using NNTP commands"""
        try:
            # Get a connection from the pool
            with self.nntp.get_connection() as conn:
                # Select the newsgroup
                conn.connection.group(newsgroup)
                
                # Try XPAT command first (most servers support this)
                try:
                    response = conn.connection._shortcmd(f'XPAT Subject 1- *{subject}*')
                    
                    if response.startswith('221'):
                        # Parse response to get message IDs
                        message_ids = []
                        lines = conn.connection._getlongresp()[1]
                        
                        for line in lines:
                            # Format is typically: article-number subject
                            parts = line.decode('utf-8', errors='ignore').split(' ', 1)
                            if len(parts) >= 1:
                                article_num = parts[0]
                                # Get message ID for article number
                                try:
                                    stat_response = conn.connection.stat(article_num)
                                    if len(stat_response) >= 2:
                                        message_ids.append(stat_response[1])
                                except:
                                    continue
                                    
                        return message_ids
                except:
                    # XPAT not supported, try XHDR
                    pass
                
                # Fallback to XHDR if XPAT not available
                return self._search_by_xhdr(conn, newsgroup, subject)
                
        except Exception as e:
            self.logger.error(f"Subject search failed: {e}")
            return []
            
    def _search_by_xhdr(self, conn, newsgroup: str, subject: str) -> List[str]:
        """Fallback search using XHDR command"""
        try:
            # Get recent articles
            response = conn.connection.group(newsgroup)
            if len(response) >= 4:
                first = int(response[2])
                last = int(response[3])
                
                # Limit search to recent articles (last 10000)
                search_start = max(first, last - 10000)
                
                # Get headers
                headers = conn.connection.xhdr('subject', f'{search_start}-{last}')
                
                message_ids = []
                for article_num, article_subject in headers[1]:
                    if subject in article_subject:
                        # Get message ID
                        try:
                            stat_response = conn.connection.stat(article_num)
                            if len(stat_response) >= 2:
                                message_ids.append(stat_response[1])
                        except:
                            continue
                            
                return message_ids
                
        except Exception as e:
            self.logger.error(f"XHDR search failed: {e}")
            return []

class RedundancyRetriever(RetrieverStrategy):
    """Redundancy-based recovery retrieval"""
    
    def __init__(self, nntp_client, db_manager):
        super().__init__(nntp_client)
        self.db = db_manager
        
    def retrieve(self, request: SegmentRequest) -> Tuple[bool, Optional[bytes], str]:
        """Retrieve using redundancy recovery"""
        if not request.redundancy_available:
            return False, None, "No redundancy data available"
            
        try:
            # Get redundancy information
            redundancy_info = self._get_redundancy_info(request)
            
            if not redundancy_info:
                return False, None, "Failed to get redundancy info"
                
            # Try to recover using redundancy
            recovered_data = self._recover_from_redundancy(
                request,
                redundancy_info
            )
            
            if recovered_data:
                # Verify hash
                actual_hash = hashlib.sha256(recovered_data).hexdigest()
                if actual_hash == request.expected_hash:
                    return True, recovered_data, ""
                else:
                    return False, None, "Recovered data hash mismatch"
            else:
                return False, None, "Redundancy recovery failed"
                
        except Exception as e:
            return False, None, str(e)
            
    def _get_redundancy_info(self, request: SegmentRequest) -> Optional[Dict]:
        """Get redundancy information for segment from database"""
        try:
            # Query database for redundant segments (segments with redundancy_index > 0)
            with self.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s2.id, s2.segment_index, s2.message_id, s2.newsgroup, 
                           s2.redundancy_index, s2.subject_hash
                    FROM segments s1
                    JOIN files f ON s1.file_id = f.id
                    JOIN segments s2 ON s2.file_id = f.id 
                        AND s2.segment_index = s1.segment_index
                        AND s2.redundancy_index > 0
                    WHERE s1.id = ?
                    ORDER BY s2.redundancy_index
                """, (request.segment_id,))
                
                redundancy_segments = []
                max_redundancy_index = 0
                
                for row in cursor:
                    redundancy_segments.append({
                        'id': row['id'],
                        'segment_index': row['segment_index'],
                        'message_id': row['message_id'],
                        'newsgroup': row['newsgroup'],
                        'redundancy_index': row['redundancy_index'],
                        'subject_hash': row['subject_hash']
                    })
                    max_redundancy_index = max(max_redundancy_index, row['redundancy_index'])
                    
                if redundancy_segments:
                    return {
                        'redundancy_level': max_redundancy_index,  # The highest redundancy_index indicates the level
                        'segments': redundancy_segments,
                        'recovery_possible': True
                    }
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get redundancy info: {e}")
            return None
            
    def _recover_from_redundancy(self, request: SegmentRequest, 
                                redundancy_info: Dict) -> Optional[bytes]:
        """Recover segment using redundancy data"""
        try:
            # Try to retrieve from redundant segments (which are exact copies)
            for red_seg in redundancy_info['segments']:
                try:
                    # Try message ID first
                    if red_seg.get('message_id'):
                        data = self.nntp.retrieve_article(
                            red_seg['message_id'],
                            red_seg['newsgroup']
                        )
                        if data:
                            # Verify if we have expected hash
                            if request.expected_hash:
                                actual_hash = hashlib.sha256(data).hexdigest()
                                if actual_hash == request.expected_hash:
                                    self.logger.info(
                                        f"Successfully recovered segment {request.segment_index} "
                                        f"from redundancy_index {red_seg['redundancy_index']}"
                                    )
                                    return data
                            else:
                                # No hash to verify, trust the data
                                return data
                                
                    # Try subject hash if message ID failed
                    if red_seg.get('subject_hash'):
                        # Use subject search retriever
                        searcher = SubjectSearchRetriever(self.nntp)
                        temp_request = SegmentRequest(
                            segment_id=str(red_seg['id']),
                            file_path=request.file_path,
                            segment_index=request.segment_index,
                            primary_message_id=None,
                            subject_hash=red_seg['subject_hash'],
                            newsgroup=red_seg['newsgroup'],
                            expected_hash=request.expected_hash,
                            expected_size=request.expected_size
                        )
                        
                        success, data, _ = searcher.retrieve(temp_request)
                        if success and data:
                            self.logger.info(
                                f"Successfully recovered segment {request.segment_index} "
                                f"from redundancy_index {red_seg['redundancy_index']} via subject search"
                            )
                            return data
                            
                except Exception as e:
                    self.logger.warning(
                        f"Failed to retrieve redundant segment {red_seg.get('id')} "
                        f"(redundancy_index={red_seg.get('redundancy_index')}): {e}"
                    )
                    continue
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Redundancy recovery failed: {e}")
            return None

class SegmentRetrievalSystem:
    """
    Intelligent segment retrieval system with fallback hierarchy
    Implements the core retrieval logic for UsenetSync
    """
    
    def __init__(self, nntp_client, db_manager, config: Dict[str, Any]):
        self.nntp = nntp_client
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Health tracking
        self.health_tracker = ServerHealthTracker()
        
        # Retrieval strategies
        self.strategies = {
            RetrievalMethod.MESSAGE_ID: MessageIDRetriever(nntp_client),
            RetrievalMethod.REDUNDANCY: RedundancyRetriever(nntp_client, db_manager),
            RetrievalMethod.SUBJECT_HASH: SubjectSearchRetriever(nntp_client)
        }
        
        # Configuration
        self.max_attempts_per_method = config.get('max_attempts_per_method', 3)
        self.method_timeout = config.get('method_timeout', 30)
        self.parallel_attempts = config.get('parallel_attempts', 2)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_retrievals': 0,
            'method_successes': {method.name: 0 for method in RetrievalMethod},
            'method_attempts': {method.name: 0 for method in RetrievalMethod},
            'total_bytes_retrieved': 0,
            'segments_requested': 0,
            'segments_retrieved': 0,
            'bytes_downloaded': 0,
            'cache_hits': 0,
            'active_requests': 0
        }
        
    def retrieve_segment(self, request: SegmentRequest) -> Tuple[bool, Optional[bytes], List[RetrievalAttempt]]:
        """
        Retrieve segment using intelligent fallback hierarchy
        Returns: (success, data, attempts_made)
        """
        self.stats['total_requests'] += 1
        self.stats['segments_requested'] += 1
        attempts = []
        
        # Try methods in order of preference
        for method in RetrievalMethod:
            if not request.can_use_method(method):
                self.logger.debug(f"Skipping {method.name} - not available for request")
                continue
                
            # Try retrieval with this method
            success, data, error = self._try_retrieval_method(request, method)
            
            # Record attempt
            attempt = RetrievalAttempt(
                method=method,
                timestamp=datetime.now(),
                success=success,
                error_message=error if not success else None,
                bytes_retrieved=len(data) if data else 0
            )
            attempts.append(attempt)
            request.attempts.append(attempt)
            
            if success and data:
                # Success!
                self.stats['successful_retrievals'] += 1
                self.stats['segments_retrieved'] += 1
                self.stats['method_successes'][method.name] += 1
                self.stats['total_bytes_retrieved'] += len(data)
                self.stats['bytes_downloaded'] += len(data)
                
                self.logger.info(
                    f"Successfully retrieved segment {request.segment_id} "
                    f"using {method.name} ({len(data)} bytes)"
                )
                
                return True, data, attempts
                
            # Log failure and continue to next method
            self.logger.warning(
                f"Failed to retrieve segment {request.segment_id} "
                f"using {method.name}: {error}"
            )
            
        # All methods failed
        self.logger.error(
            f"Failed to retrieve segment {request.segment_id} "
            f"after {len(attempts)} attempts"
        )
        
        return False, None, attempts
        
    def _try_retrieval_method(self, request: SegmentRequest, 
                             method: RetrievalMethod) -> Tuple[bool, Optional[bytes], str]:
        """Try retrieval using specific method"""
        start_time = time.time()
        self.stats['method_attempts'][method.name] += 1
        
        try:
            # Get strategy
            strategy = self.strategies.get(method)
            if not strategy:
                return False, None, f"No strategy for {method.name}"
                
            # Direct retrieval using strategy
            success, data, error = strategy.retrieve(request)
            
            # Record performance
            duration = time.time() - start_time
            
            # Track server health (use default server for now)
            self.health_tracker.record_attempt(
                "default", success, duration, method
            )
            
            if success:
                return True, data, ""
            else:
                return False, None, error
                
        except Exception as e:
            return False, None, str(e)
        
    def batch_retrieve(self, requests: List[SegmentRequest], 
                      progress_callback: Optional[Callable] = None) -> Dict[str, Tuple[bool, Optional[bytes]]]:
        """
        Retrieve multiple segments efficiently
        Returns: dict mapping segment_id to (success, data)
        """
        results = {}
        
        # Sort by priority
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)
        
        # Process in batches for efficiency
        batch_size = self.config.get('batch_size', 10)
        
        for i in range(0, len(sorted_requests), batch_size):
            batch = sorted_requests[i:i + batch_size]
            
            # Process batch
            for request in batch:
                success, data, _ = self.retrieve_segment(request)
                results[request.segment_id] = (success, data)
                
                # Progress callback
                if progress_callback:
                    progress_callback({
                        'current': len(results),
                        'total': len(requests),
                        'segment_id': request.segment_id,
                        'success': success
                    })
                    
        return results
        
    def optimize_retrieval_order(self, requests: List[SegmentRequest]) -> List[SegmentRequest]:
        """
        Optimize retrieval order based on various factors
        """
        # Score each request
        scored_requests = []
        
        for request in requests:
            score = self._calculate_retrieval_score(request)
            scored_requests.append((score, request))
            
        # Sort by score (higher score = higher priority)
        scored_requests.sort(reverse=True)
        
        return [request for _, request in scored_requests]
        
    def _calculate_retrieval_score(self, request: SegmentRequest) -> float:
        """Calculate retrieval score for prioritization"""
        score = 0.0
        
        # Base priority
        score += (10 - request.priority) * 10
        
        # Availability of methods
        if request.primary_message_id:
            score += 50  # Direct retrieval possible
        if request.redundancy_available:
            score += 30  # Redundancy available
        if request.subject_hash:
            score += 10  # Subject search possible
            
        # Previous attempts (deprioritize if many failures)
        score -= len(request.attempts) * 5
        
        # Size factor - smaller segments often download faster
        if request.expected_size < 100000:  # < 100KB
            score += 5
        elif request.expected_size > 1000000:  # > 1MB
            score -= 5
            
        # Segment index - prioritize early segments for streaming
        if hasattr(request, 'segment_index'):
            if request.segment_index < 5:  # First 5 segments
                score += 10
                
        return score
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        stats = self.stats.copy()
        
        # Calculate success rates
        if stats['total_requests'] > 0:
            stats['overall_success_rate'] = (
                stats['successful_retrievals'] / stats['total_requests'] * 100
            )
        else:
            stats['overall_success_rate'] = 0
            
        # Method success rates
        stats['method_success_rates'] = {}
        for method in RetrievalMethod:
            attempts = stats['method_attempts'][method.name]
            if attempts > 0:
                rate = stats['method_successes'][method.name] / attempts * 100
                stats['method_success_rates'][method.name] = rate
            else:
                stats['method_success_rates'][method.name] = 0
                
        # Server health
        stats['server_health'] = self._get_server_health_summary()
        
        return stats
        
    def _get_server_health_summary(self) -> Dict[str, Any]:
        """Get summary of server health"""
        summary = {}
        
        for server, stats in self.health_tracker.server_stats.items():
            if stats['total_attempts'] > 0:
                success_rate = stats['successful_attempts'] / stats['total_attempts'] * 100
                avg_response = (
                    stats['total_response_time'] / stats['successful_attempts']
                    if stats['successful_attempts'] > 0 else 0
                )
                
                summary[server] = {
                    'success_rate': success_rate,
                    'avg_response_time': avg_response,
                    'last_success': stats['last_success'].isoformat() if stats['last_success'] else None,
                    'last_failure': stats['last_failure'].isoformat() if stats['last_failure'] else None
                }
                
        return summary
        
    def clear_statistics(self):
        """Clear statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_retrievals': 0,
            'method_successes': {method.name: 0 for method in RetrievalMethod},
            'method_attempts': {method.name: 0 for method in RetrievalMethod},
            'total_bytes_retrieved': 0,
            'segments_requested': 0,
            'segments_retrieved': 0,
            'bytes_downloaded': 0,
            'cache_hits': 0,
            'active_requests': 0
        }
