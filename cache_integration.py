#!/usr/bin/env python3
"""
Enhanced Cache Integration for UsenetSync
Complete integration with memory optimization and performance monitoring
"""

import hashlib
import base64
import time
import logging
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

def integrate_cache_into_download_system(app):
    """
    Add enhanced encrypted caching to existing download system
    
    Args:
        app: The main UsenetSync application instance
    """
    try:
        from encrypted_index_cache import EnhancedEncryptedIndexCache
        
        # Create enhanced cache instance
        cache = EnhancedEncryptedIndexCache(app.db)
        
        if not cache.enabled:
            logger.warning("Enhanced cache disabled - cryptography library not available")
            return app
        
        # Store references for access
        app.download_system.index_cache = cache
        app.index_cache = cache  # For CLI access
        
        # Apply integration patches
        _patch_download_system(app.download_system)
        
        logger.info("Enhanced encrypted index cache integrated successfully")
        logger.info(f"Memory cache: {cache.max_memory_entries} entries max")
        logger.info("Features: Memory LRU + SQLite + Performance monitoring + Auto-cleanup")
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to integrate enhanced cache: {e}")
        # Don't fail the entire application if cache integration fails
        return app

def _patch_download_system(download_system):
    """Apply patches to add enhanced caching with full share type support"""
    
    # Store original methods to chain functionality
    download_system._original_download_from_access_string = download_system.download_from_access_string
    download_system._original_parse_index = download_system._parse_index
    
    # Enhanced download method with intelligent caching
    def download_from_access_string_with_enhanced_cache(access_string: str, 
                                                       destination_path: str,
                                                       password: Optional[str] = None) -> str:
        """Enhanced download with memory + SQLite caching for all share types"""
        cache_start_time = time.time()
        
        try:
            # Parse access string to get folder information
            access_data = download_system.security.decode_access_string(access_string)
            folder_id = access_data.get('folder_id')
            share_type = access_data.get('share_type', 'unknown')
            
            logger.debug(f"Enhanced cache check for folder {folder_id} ({share_type})")
            
            # Get user ID for private shares
            user_id = None
            if share_type == 'private':
                user_id = download_system.security.get_user_id()
                if not user_id:
                    logger.debug("No user ID available for private share caching")
                    return download_system._original_download_from_access_string(
                        access_string, destination_path, password
                    )
            
            # Generate cache key and derive encryption key
            cache_key, encryption_key = _generate_cache_keys(
                download_system, folder_id, share_type, user_id, password
            )
            
            # Attempt enhanced cache retrieval
            if cache_key and encryption_key and hasattr(download_system, 'index_cache'):
                cached_data = download_system.index_cache.get(cache_key, encryption_key)
                
                if cached_data:
                    cache_elapsed = time.time() - cache_start_time
                    
                    # Check if this was a memory cache hit (very fast response)
                    cache_type = "Memory" if cache_elapsed < 0.01 else "Database"
                    
                    logger.info(
                        f"Enhanced Cache {cache_type} HIT: {folder_id} ({share_type}) - "
                        f"{cached_data.get('total_files', 0):,} files "
                        f"({cache_elapsed*1000:.1f}ms)"
                    )
                    
                    # Start download using cached data
                    return _start_download_with_cached_data(
                        download_system, cached_data, access_string, destination_path
                    )
                else:
                    cache_elapsed = time.time() - cache_start_time
                    logger.debug(f"Enhanced Cache MISS: {folder_id} ({cache_elapsed*1000:.1f}ms)")
            
            # Store context for caching after successful download
            download_system._cache_context = {
                'folder_id': folder_id,
                'share_type': share_type,
                'cache_key': cache_key,
                'encryption_key': encryption_key,
                'user_id': user_id,
                'access_string': access_string,
                'cache_start_time': cache_start_time
            }
            
        except Exception as e:
            logger.debug(f"Enhanced cache check failed: {e}")
            # Clear any partial context
            if hasattr(download_system, '_cache_context'):
                delattr(download_system, '_cache_context')
        
        # Proceed with normal download (will cache on successful parse)
        return download_system._original_download_from_access_string(
            access_string, destination_path, password
        )
    
    # Enhanced index parsing with automatic caching
    def parse_index_with_enhanced_cache(index_data: Dict) -> Dict:
        """Parse index and automatically cache with performance tracking"""
        parse_start_time = time.time()
        
        # Parse using original method first
        parsed = download_system._original_parse_index(index_data)
        
        # Attempt to cache if we have the context from download
        try:
            cache_context = getattr(download_system, '_cache_context', None)
            
            if cache_context and parsed and hasattr(download_system, 'index_cache'):
                folder_id = cache_context['folder_id']
                share_type = cache_context['share_type']
                cache_key = cache_context['cache_key']
                encryption_key = cache_context['encryption_key']
                cache_start_time = cache_context.get('cache_start_time', time.time())
                
                if cache_key and encryption_key:
                    # Ensure required fields are present
                    if 'id' not in parsed:
                        parsed['id'] = folder_id
                    if 'folder_id' not in parsed:
                        parsed['folder_id'] = folder_id
                    
                    # Cache the successfully parsed index
                    store_start_time = time.time()
                    success = download_system.index_cache.store(
                        folder_id, parsed, cache_key, share_type, encryption_key
                    )
                    store_elapsed = time.time() - store_start_time
                    
                    if success:
                        total_cache_time = time.time() - cache_start_time
                        logger.info(
                            f"Enhanced cache store: {share_type} index for folder {folder_id} "
                            f"(store: {store_elapsed*1000:.1f}ms, total: {total_cache_time*1000:.1f}ms)"
                        )
                        
                        # Log performance metrics
                        cache_stats = download_system.index_cache.get_stats()
                        logger.debug(
                            f"Cache stats - Memory: {cache_stats.get('memory_cache_entries', 0)}/{cache_stats.get('memory_cache_max', 0)}, "
                            f"Hit rate: {cache_stats.get('overall_hit_rate', 0):.1f}%, "
                            f"Total entries: {cache_stats.get('current_entries', 0):,}"
                        )
                    else:
                        logger.warning(f"Enhanced cache store failed for folder {folder_id}")
                
        except Exception as e:
            logger.debug(f"Enhanced cache store failed: {e}")
        
        # Clean up cache context
        if hasattr(download_system, '_cache_context'):
            delattr(download_system, '_cache_context')
        
        parse_elapsed = time.time() - parse_start_time
        logger.debug(f"Index parse completed in {parse_elapsed*1000:.1f}ms")
        
        return parsed
    
    # Apply the enhanced patches
    download_system.download_from_access_string = download_from_access_string_with_enhanced_cache
    download_system._parse_index = parse_index_with_enhanced_cache
    
    # Add enhanced utility methods for cache management
    download_system.clear_cache = lambda folder_id=None: (
        download_system.index_cache.clear(folder_id) 
        if hasattr(download_system, 'index_cache') else None
    )
    
    download_system.get_cache_stats = lambda: (
        download_system.index_cache.get_stats() 
        if hasattr(download_system, 'index_cache') else {}
    )
    
    download_system.optimize_cache = lambda max_size_mb=1000, max_age_days=30: (
        download_system.index_cache.optimize_for_scale(max_size_mb, max_age_days)
        if hasattr(download_system, 'index_cache') else None
    )

def _generate_cache_keys(download_system, folder_id: str, share_type: str,
                        user_id: Optional[str], password: Optional[str]) -> Tuple[Optional[str], Optional[bytes]]:
    """Generate cache key and encryption key based on share type"""
    try:
        if share_type == 'public':
            # Public shares: derive key from folder_id
            cache_key = download_system.index_cache.generate_cache_key(
                folder_id, share_type
            )
            # Use folder_id as basis for encryption key
            encryption_key = hashlib.pbkdf2_hmac(
                'sha256',
                folder_id.encode('utf-8'),
                b'public_share_cache',
                iterations=100000,
                dklen=32
            )
            return cache_key, encryption_key
            
        elif share_type == 'private' and user_id:
            # Private shares: use user-specific key derivation
            cache_key = download_system.index_cache.generate_cache_key(
                folder_id, share_type, user_id=user_id
            )
            # Derive key from user_id and folder_id (matching security system)
            encryption_key = hashlib.pbkdf2_hmac(
                'sha256',
                (user_id + folder_id).encode('utf-8'),
                b'private_share_cache',
                iterations=100000,
                dklen=32
            )
            return cache_key, encryption_key
            
        elif share_type == 'protected' and password:
            # Protected shares: derive from password (matching security system)
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            cache_key = download_system.index_cache.generate_cache_key(
                folder_id, share_type, password_hash=password_hash
            )
            # Use same derivation as security system for consistency
            encryption_key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                folder_id.encode('utf-8'),
                iterations=100000,
                dklen=32
            )
            return cache_key, encryption_key
            
    except Exception as e:
        logger.debug(f"Failed to generate cache keys for {folder_id}: {e}")
    
    return None, None

def _start_download_with_cached_data(download_system, cached_data: Dict,
                                   access_string: str, destination_path: str) -> str:
    """Start download session using cached index data"""
    try:
        # Create session ID
        session_id = hashlib.sha256(
            f"{access_string}:{time.time()}".encode('utf-8')
        ).hexdigest()[:16]
        
        # Import required classes (handle import variations)
        try:
            from enhanced_download_system import DownloadSession, FileDownload
        except ImportError:
            try:
                from download_system import DownloadSession, FileDownload
            except ImportError:
                logger.error("Could not import DownloadSession/FileDownload classes")
                raise
        
        # Create download session using cached data
        session = DownloadSession(
            session_id=session_id,
            access_string=access_string,
            folder_name=cached_data.get('name', 'Unknown Folder'),
            folder_id=cached_data.get('folder_id', cached_data.get('id', '')),
            destination_path=destination_path,
            total_files=len(cached_data.get('files', [])),
            total_size=cached_data.get('total_size', 0)
        )
        
        # Create file download entries from cached data
        for file_info in cached_data.get('files', []):
            file_download = FileDownload(
                file_path=file_info['path'],
                file_size=file_info['size'],
                file_hash=file_info.get('hash', ''),
                segment_count=len(file_info.get('segments', []))
            )
            session.file_downloads[file_info['path']] = file_download
        
        # Register session in download system
        with download_system._session_lock:
            download_system.active_sessions[session_id] = session
        
        # Save session to database
        download_system.db.create_download_session(
            session_id,
            access_string,
            session.folder_name,
            session.total_files,
            session.total_size
        )
        
        # Start download using cached folder information
        download_system._start_session_download(session, cached_data)
        
        logger.info(f"Started enhanced download from cache: session {session_id}")
        
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to start download with cached data: {e}")
        # Fallback to normal download
        return download_system._original_download_from_access_string(
            access_string, destination_path, None
        )

def add_cache_commands(cli):
    """Add enhanced cache management commands to CLI"""
    try:
        import click
        
        @cli.group()
        def cache():
            """Manage enhanced encrypted index cache"""
            pass
        
        @cache.command()
        @click.pass_context
        def stats(ctx):
            """Show comprehensive enhanced cache statistics"""
            app = ctx.obj
            if not hasattr(app, 'index_cache'):
                click.echo("Enhanced cache not available")
                return
                
            stats = app.index_cache.get_stats()
            
            if not stats.get('enabled', False):
                click.echo(f"Enhanced cache disabled: {stats.get('reason', 'Unknown reason')}")
                return
            
            click.echo("Enhanced Index Cache Statistics")
            click.echo("=" * 60)
            click.echo(f"Unique folders: {stats['unique_folders']:,}")
            click.echo(f"Current cache entries: {stats['current_entries']:,}")
            click.echo(f"Current cache size: {stats['current_size_mb']:.1f} MB")
            click.echo(f"Total files cached: {stats['total_files_cached']:,}")
            click.echo(f"Average entry size: {stats['avg_entry_size_kb']:.1f} KB")
            click.echo(f"Largest entry: {stats['max_entry_size_kb']:.1f} KB")
            click.echo("")
            
            # Performance metrics
            click.echo("Performance Metrics:")
            click.echo(f"  Total requests: {stats['total_requests']:,}")
            click.echo(f"  Overall hit rate: {stats['overall_hit_rate']:.1f}%")
            click.echo(f"  Memory hit rate: {stats['memory_hit_rate']:.1f}% ({stats['memory_hits']:,} hits)")
            click.echo(f"  Database hits: {stats['db_hits']:,}")
            click.echo(f"  Cache misses: {stats['db_misses']:,}")
            click.echo("")
            
            # Memory cache status
            click.echo("Memory Cache:")
            click.echo(f"  Current entries: {stats['memory_cache_entries']}/{stats['memory_cache_max']}")
            click.echo(f"  Evictions: {stats['memory_evictions']:,}")
            click.echo("")
            
            # Access patterns
            click.echo("Access Patterns:")
            click.echo(f"  Average access count: {stats['avg_access_count']:.1f}")
            click.echo(f"  Most accessed: {stats['max_access_count']:,} times")
        
        @cache.command()
        @click.pass_context
        def clear(ctx):
            """Clear enhanced cache"""
            app = ctx.obj
            if not hasattr(app, 'index_cache'):
                click.echo("Enhanced cache not available")
                return
            
            if click.confirm("Clear all cached indices?"):
                app.index_cache.clear()
                click.echo("Cleared all cached indices")
        
        @cache.command()
        @click.pass_context
        def optimize(ctx):
            """Optimize enhanced cache"""
            app = ctx.obj
            if not hasattr(app, 'index_cache'):
                click.echo("Enhanced cache not available")
                return
            
            click.echo("Optimizing enhanced cache...")
            app.index_cache.optimize_for_scale()
            click.echo("Enhanced cache optimization complete")
        
        return cli
        
    except ImportError:
        logger.warning("Click not available - enhanced cache CLI commands not added")
        return cli
