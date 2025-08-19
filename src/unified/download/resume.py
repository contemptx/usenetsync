#!/usr/bin/env python3
"""
Unified Resume - Resume interrupted downloads
Production-ready with state persistence
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DownloadState:
    """Download state for resume capability"""
    
    def __init__(self, download_id: str, file_info: Dict[str, Any]):
        self.download_id = download_id
        self.file_info = file_info
        self.total_segments = file_info.get('total_segments', 0)
        self.completed_segments = set()
        self.failed_segments = set()
        self.partial_file_path = None
        self.started_at = datetime.now()
        self.last_updated = datetime.now()
        self.bytes_downloaded = 0
        self.status = 'downloading'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            'download_id': self.download_id,
            'file_info': self.file_info,
            'total_segments': self.total_segments,
            'completed_segments': list(self.completed_segments),
            'failed_segments': list(self.failed_segments),
            'partial_file_path': self.partial_file_path,
            'started_at': self.started_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'bytes_downloaded': self.bytes_downloaded,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadState':
        """Create from dictionary"""
        state = cls(data['download_id'], data['file_info'])
        state.total_segments = data['total_segments']
        state.completed_segments = set(data.get('completed_segments', []))
        state.failed_segments = set(data.get('failed_segments', []))
        state.partial_file_path = data.get('partial_file_path')
        state.bytes_downloaded = data.get('bytes_downloaded', 0)
        state.status = data.get('status', 'downloading')
        
        if 'started_at' in data:
            state.started_at = datetime.fromisoformat(data['started_at'])
        if 'last_updated' in data:
            state.last_updated = datetime.fromisoformat(data['last_updated'])
        
        return state

class UnifiedResume:
    """
    Unified download resume capability
    Handles interrupted downloads and state persistence
    """
    
    def __init__(self, state_dir: str = '.download_states'):
        """Initialize resume handler"""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.states = {}  # download_id -> DownloadState
        
        # Load existing states
        self._load_states()
    
    def create_download(self, download_id: str, file_info: Dict[str, Any]) -> DownloadState:
        """
        Create new download state
        
        Args:
            download_id: Unique download identifier
            file_info: File information
        
        Returns:
            Download state
        """
        state = DownloadState(download_id, file_info)
        self.states[download_id] = state
        self._save_state(state)
        
        logger.info(f"Created download state: {download_id}")
        return state
    
    def update_progress(self, download_id: str, segment_index: int,
                       success: bool, bytes_downloaded: int = 0):
        """
        Update download progress
        
        Args:
            download_id: Download identifier
            segment_index: Segment index
            success: Whether segment downloaded successfully
            bytes_downloaded: Bytes downloaded
        """
        if download_id not in self.states:
            logger.warning(f"Unknown download: {download_id}")
            return
        
        state = self.states[download_id]
        
        if success:
            state.completed_segments.add(segment_index)
            state.failed_segments.discard(segment_index)
            state.bytes_downloaded += bytes_downloaded
        else:
            state.failed_segments.add(segment_index)
        
        state.last_updated = datetime.now()
        
        # Check if complete
        if len(state.completed_segments) == state.total_segments:
            state.status = 'completed'
            logger.info(f"Download completed: {download_id}")
        
        self._save_state(state)
    
    def get_remaining_segments(self, download_id: str) -> List[int]:
        """
        Get list of remaining segments to download
        
        Args:
            download_id: Download identifier
        
        Returns:
            List of segment indices
        """
        if download_id not in self.states:
            return []
        
        state = self.states[download_id]
        all_segments = set(range(state.total_segments))
        remaining = all_segments - state.completed_segments
        
        return sorted(list(remaining))
    
    def can_resume(self, download_id: str) -> bool:
        """
        Check if download can be resumed
        
        Args:
            download_id: Download identifier
        
        Returns:
            True if download can be resumed
        """
        if download_id not in self.states:
            return False
        
        state = self.states[download_id]
        return state.status in ['downloading', 'paused', 'failed']
    
    def pause_download(self, download_id: str):
        """Pause download"""
        if download_id in self.states:
            self.states[download_id].status = 'paused'
            self._save_state(self.states[download_id])
            logger.info(f"Download paused: {download_id}")
    
    def resume_download(self, download_id: str) -> Optional[DownloadState]:
        """
        Resume download
        
        Args:
            download_id: Download identifier
        
        Returns:
            Download state or None
        """
        if not self.can_resume(download_id):
            return None
        
        state = self.states[download_id]
        state.status = 'downloading'
        state.last_updated = datetime.now()
        self._save_state(state)
        
        logger.info(f"Resuming download: {download_id} ({len(state.completed_segments)}/{state.total_segments} segments)")
        return state
    
    def cancel_download(self, download_id: str):
        """Cancel and clean up download"""
        if download_id in self.states:
            state = self.states[download_id]
            state.status = 'cancelled'
            
            # Clean up partial file
            if state.partial_file_path and os.path.exists(state.partial_file_path):
                os.remove(state.partial_file_path)
            
            # Remove state file
            state_file = self.state_dir / f"{download_id}.json"
            if state_file.exists():
                state_file.unlink()
            
            del self.states[download_id]
            logger.info(f"Download cancelled: {download_id}")
    
    def get_download_progress(self, download_id: str) -> Dict[str, Any]:
        """Get download progress information"""
        if download_id not in self.states:
            return {}
        
        state = self.states[download_id]
        
        return {
            'download_id': download_id,
            'status': state.status,
            'total_segments': state.total_segments,
            'completed_segments': len(state.completed_segments),
            'failed_segments': len(state.failed_segments),
            'progress_percent': (len(state.completed_segments) / state.total_segments * 100) if state.total_segments > 0 else 0,
            'bytes_downloaded': state.bytes_downloaded,
            'started_at': state.started_at.isoformat(),
            'last_updated': state.last_updated.isoformat()
        }
    
    def _save_state(self, state: DownloadState):
        """Save state to disk"""
        state_file = self.state_dir / f"{state.download_id}.json"
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_states(self):
        """Load states from disk"""
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                
                state = DownloadState.from_dict(data)
                self.states[state.download_id] = state
                
            except Exception as e:
                logger.error(f"Failed to load state from {state_file}: {e}")
        
        if self.states:
            logger.info(f"Loaded {len(self.states)} download states")