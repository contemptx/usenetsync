"""Log management system for UsenetSync."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
import gzip
import shutil

class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    """Represents a single log entry."""
    id: str
    timestamp: datetime
    level: LogLevel
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
class LogManager:
    """Manages application logging and log storage."""
    
    def __init__(self, db_manager, log_dir: Path = None):
        self.db = db_manager
        self.log_dir = log_dir or Path("/var/log/usenetsync")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer for recent logs
        self.log_buffer: List[LogEntry] = []
        self.buffer_size = 1000
        
        # Configure Python logging
        self._setup_logging()
        
        # Start background tasks
        self.tasks = []
        
    def _setup_logging(self):
        """Configure Python logging system."""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            self.log_dir / f"usenetsync_{datetime.now():%Y%m%d}.log"
        )
        file_handler.setFormatter(formatter)
        
        # Error file handler
        error_handler = logging.FileHandler(
            self.log_dir / f"errors_{datetime.now():%Y%m%d}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
    async def start(self):
        """Start log management background tasks."""
        self.tasks = [
            asyncio.create_task(self._flush_logs_periodically()),
            asyncio.create_task(self._rotate_logs_daily()),
            asyncio.create_task(self._cleanup_old_logs())
        ]
        
    async def stop(self):
        """Stop background tasks."""
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
    async def log(
        self,
        level: LogLevel,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Create a log entry.
        
        Args:
            level: Log severity level
            category: Log category (e.g., Upload, Download, Network)
            message: Log message
            details: Additional structured data
            source: Source component/module
            user_id: Associated user ID
            session_id: Associated session ID
        """
        entry = LogEntry(
            id=self._generate_log_id(),
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details,
            source=source,
            user_id=user_id,
            session_id=session_id
        )
        
        # Add to buffer
        self.log_buffer.append(entry)
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)
        
        # Write to file
        await self._write_to_file(entry)
        
        # Store in database if error or critical
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            await self._store_in_db(entry)
            
        # Also use Python logging
        logger = logging.getLogger(category)
        log_method = getattr(logger, level.value)
        log_method(message, extra={'details': details})
        
    async def get_logs(
        self,
        level: Optional[LogLevel] = None,
        category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs with filtering.
        
        Args:
            level: Filter by log level (and above)
            category: Filter by category
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of logs to return
            offset: Pagination offset
            search: Search in message and details
            
        Returns:
            List of log entries
        """
        # First check buffer for recent logs
        filtered = self.log_buffer.copy()
        
        # Apply filters
        if level:
            level_priority = self._get_level_priority(level)
            filtered = [
                log for log in filtered
                if self._get_level_priority(log.level) >= level_priority
            ]
            
        if category:
            filtered = [log for log in filtered if log.category == category]
            
        if start_time:
            filtered = [log for log in filtered if log.timestamp >= start_time]
            
        if end_time:
            filtered = [log for log in filtered if log.timestamp <= end_time]
            
        if search:
            search_lower = search.lower()
            filtered = [
                log for log in filtered
                if search_lower in log.message.lower() or
                (log.details and search_lower in json.dumps(log.details).lower())
            ]
        
        # Sort by timestamp descending
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        filtered = filtered[offset:offset + limit]
        
        # Convert to dict
        return [self._log_to_dict(log) for log in filtered]
    
    async def get_log_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get log statistics.
        
        Returns:
            Statistics about logs
        """
        if not start_time:
            start_time = datetime.now() - timedelta(days=7)
        if not end_time:
            end_time = datetime.now()
            
        # Query database for statistics
        query = """
            SELECT 
                level,
                category,
                COUNT(*) as count,
                MIN(timestamp) as first_log,
                MAX(timestamp) as last_log
            FROM logs
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY level, category
        """
        
        rows = await self.db.fetch_all(query, (start_time, end_time))
        
        # Process statistics
        stats = {
            'total_logs': 0,
            'by_level': {},
            'by_category': {},
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }
        
        for row in rows:
            count = row['count']
            level = row['level']
            category = row['category']
            
            stats['total_logs'] += count
            
            if level not in stats['by_level']:
                stats['by_level'][level] = 0
            stats['by_level'][level] += count
            
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += count
            
        # Add error rate
        error_count = stats['by_level'].get('error', 0) + stats['by_level'].get('critical', 0)
        stats['error_rate'] = (error_count / stats['total_logs'] * 100) if stats['total_logs'] > 0 else 0
        
        return stats
    
    async def clear_logs(
        self,
        before_date: Optional[datetime] = None,
        level: Optional[LogLevel] = None,
        category: Optional[str] = None
    ) -> int:
        """
        Clear logs based on criteria.
        
        Returns:
            Number of logs deleted
        """
        conditions = []
        params = []
        
        if before_date:
            conditions.append("timestamp < ?")
            params.append(before_date)
            
        if level:
            conditions.append("level = ?")
            params.append(level.value)
            
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if not conditions:
            # Clear all logs
            query = "DELETE FROM logs"
            params = []
        else:
            query = f"DELETE FROM logs WHERE {' AND '.join(conditions)}"
            
        result = await self.db.execute(query, params)
        
        # Clear buffer if clearing all
        if not conditions:
            self.log_buffer.clear()
            
        return result.rowcount if hasattr(result, 'rowcount') else 0
    
    async def export_logs(
        self,
        filepath: Path,
        format: str = 'json',
        compress: bool = True,
        **filters
    ) -> bool:
        """
        Export logs to file.
        
        Args:
            filepath: Export file path
            format: Export format (json, csv, txt)
            compress: Compress the export file
            **filters: Log filters
            
        Returns:
            Success status
        """
        try:
            logs = await self.get_logs(**filters)
            
            if format == 'json':
                content = json.dumps(logs, indent=2, default=str)
            elif format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                if logs:
                    writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
                content = output.getvalue()
            else:  # txt
                lines = []
                for log in logs:
                    line = f"[{log['timestamp']}] [{log['level'].upper()}] [{log['category']}] {log['message']}"
                    if log.get('details'):
                        line += f"\n  Details: {json.dumps(log['details'])}"
                    lines.append(line)
                content = '\n'.join(lines)
            
            # Write to file
            if compress:
                with gzip.open(filepath.with_suffix('.gz'), 'wt') as f:
                    f.write(content)
            else:
                async with aiofiles.open(filepath, 'w') as f:
                    await f.write(content)
                    
            return True
            
        except Exception as e:
            logging.error(f"Failed to export logs: {e}")
            return False
    
    def _generate_log_id(self) -> str:
        """Generate unique log ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_level_priority(self, level: LogLevel) -> int:
        """Get numeric priority for log level."""
        priorities = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return priorities.get(level, 0)
    
    def _log_to_dict(self, log: LogEntry) -> Dict[str, Any]:
        """Convert LogEntry to dictionary."""
        data = asdict(log)
        data['level'] = log.level.value
        data['timestamp'] = log.timestamp.isoformat()
        return data
    
    async def _write_to_file(self, entry: LogEntry):
        """Write log entry to file."""
        filename = self.log_dir / f"{entry.category.lower()}_{datetime.now():%Y%m%d}.log"
        
        log_line = json.dumps(self._log_to_dict(entry)) + '\n'
        
        async with aiofiles.open(filename, 'a') as f:
            await f.write(log_line)
    
    async def _store_in_db(self, entry: LogEntry):
        """Store log entry in database."""
        query = """
            INSERT INTO logs 
            (id, timestamp, level, category, message, details, source, user_id, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.db.execute(query, (
            entry.id,
            entry.timestamp,
            entry.level.value,
            entry.category,
            entry.message,
            json.dumps(entry.details) if entry.details else None,
            entry.source,
            entry.user_id,
            entry.session_id
        ))
    
    async def _flush_logs_periodically(self):
        """Periodically flush logs to database."""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Store warning and above logs
                for log in self.log_buffer:
                    if self._get_level_priority(log.level) >= 2:  # WARNING and above
                        await self._store_in_db(log)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error flushing logs: {e}")
    
    async def _rotate_logs_daily(self):
        """Rotate log files daily."""
        while True:
            try:
                # Wait until next day
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                await asyncio.sleep((tomorrow - now).total_seconds())
                
                # Rotate logs
                for log_file in self.log_dir.glob("*.log"):
                    if log_file.stat().st_size > 0:
                        # Compress old log
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        log_file.unlink()
                        
                # Reconfigure logging
                self._setup_logging()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error rotating logs: {e}")
    
    async def _cleanup_old_logs(self):
        """Clean up old log files."""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                
                # Delete logs older than 30 days
                cutoff = datetime.now() - timedelta(days=30)
                
                # Clean database
                await self.clear_logs(before_date=cutoff)
                
                # Clean files
                for log_file in self.log_dir.glob("*.gz"):
                    if log_file.stat().st_mtime < cutoff.timestamp():
                        log_file.unlink()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error cleaning logs: {e}")

# Convenience functions for quick logging
async def log_info(manager: LogManager, category: str, message: str, **kwargs):
    """Log info message."""
    await manager.log(LogLevel.INFO, category, message, **kwargs)

async def log_warning(manager: LogManager, category: str, message: str, **kwargs):
    """Log warning message."""
    await manager.log(LogLevel.WARNING, category, message, **kwargs)

async def log_error(manager: LogManager, category: str, message: str, **kwargs):
    """Log error message."""
    await manager.log(LogLevel.ERROR, category, message, **kwargs)

async def log_critical(manager: LogManager, category: str, message: str, **kwargs):
    """Log critical message."""
    await manager.log(LogLevel.CRITICAL, category, message, **kwargs)