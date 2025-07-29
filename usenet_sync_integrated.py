#!/usr/bin/env python3
"""
UsenetSync - Integrated file monitoring and NNTP posting
Monitors directories and automatically posts files to Usenet
"""
# Fix Windows console encoding
import sys
import io
if sys.platform == 'win32':
    # Set console encoding to UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')



import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from production_nntp_client import ProductionNNTPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('usenet_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UsenetSyncHandler(FileSystemEventHandler):
    """Handle file system events and post to Usenet"""
    
    def __init__(self, nntp_client, config):
        self.client = nntp_client
        self.config = config
        self.posted_files = set()
        self.load_posted_files()
        
    def load_posted_files(self):
        """Load list of already posted files"""
        posted_file = Path(self.config.get('posted_files_log', 'posted_files.json'))
        if posted_file.exists():
            try:
                with open(posted_file, 'r') as f:
                    self.posted_files = set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading posted files: {e}")
    
    def save_posted_files(self):
        """Save list of posted files"""
        posted_file = Path(self.config.get('posted_files_log', 'posted_files.json'))
        try:
            with open(posted_file, 'w') as f:
                json.dump(list(self.posted_files), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving posted files: {e}")
    
    def should_post_file(self, file_path):
        """Check if file should be posted"""
        # Check if already posted
        if str(file_path) in self.posted_files:
            return False
        
        # Check file extensions
        allowed_extensions = self.config.get('allowed_extensions', [])
        if allowed_extensions:
            if not any(file_path.suffix.lower() == ext.lower() for ext in allowed_extensions):
                return False
        
        # Check file size
        min_size = self.config.get('min_file_size', 0)
        max_size = self.config.get('max_file_size', 0)
        
        try:
            file_size = file_path.stat().st_size
            if min_size > 0 and file_size < min_size:
                return False
            if max_size > 0 and file_size > max_size:
                return False
        except:
            return False
        
        return True
    
    def get_newsgroup_for_file(self, file_path):
        """Determine appropriate newsgroup based on file type"""
        newsgroup_map = self.config.get('newsgroup_map', {})
        
        # Check file extension
        ext = file_path.suffix.lower()
        for pattern, newsgroup in newsgroup_map.items():
            if pattern.startswith('*') and ext == pattern[1:]:
                return newsgroup
        
        # Default newsgroup
        return self.config.get('default_newsgroup', 'alt.binaries.test')
    
    def post_file(self, file_path):
        """Post a file to Usenet"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists() or not file_path.is_file():
                return False
            
            if not self.should_post_file(file_path):
                logger.debug(f"Skipping file: {file_path}")
                return False
            
            # Get file info
            file_size = file_path.stat().st_size
            file_name = file_path.name
            newsgroup = self.get_newsgroup_for_file(file_path)
            
            # Create subject
            subject_template = self.config.get('subject_template', '{filename} - {size}')
            subject = subject_template.format(
                filename=file_name,
                size=self.format_size(file_size),
                date=datetime.now().strftime('%Y%m%d'),
                time=datetime.now().strftime('%H%M%S')
            )
            
            logger.info(f"Posting file: {file_name} ({self.format_size(file_size)}) to {newsgroup}")
            
            # Post the file
            start_time = time.time()
            success, response = self.client.post_file(
                file_path=str(file_path),
                subject=subject,
                newsgroup=newsgroup,
                from_user=self.config.get('from_user', 'usenet-sync@auto.post'),
                extra_headers={
                    'X-File-Name': file_name,
                    'X-File-Size': str(file_size),
                    'X-Posted-By': 'UsenetSync/1.0'
                }
            )
            
            post_time = time.time() - start_time
            
            if success:
                logger.info(f"[OK] Successfully posted {file_name} in {post_time:.2f}s ({file_size/post_time/1024/1024:.2f} MB/s)")
                logger.info(f"  Message ID: {response}")
                
                # Mark as posted
                self.posted_files.add(str(file_path))
                self.save_posted_files()
                
                # Log to posting history
                self.log_posting(file_path, newsgroup, response, post_time)
                
                return True
            else:
                logger.error(f"[FAIL] Failed to post {file_name}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error posting file {file_path}: {e}")
            logger.exception("Posting exception")
            return False
    
    def log_posting(self, file_path, newsgroup, message_id, post_time):
        """Log successful posting"""
        log_file = Path(self.config.get('posting_log', 'posting_history.log'))
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()}\t{file_path}\t{newsgroup}\t{message_id}\t{post_time:.2f}\n")
        except Exception as e:
            logger.error(f"Error logging posting: {e}")
    
    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def on_created(self, event):
        """Handle file creation event"""
        if not event.is_directory:
            logger.debug(f"New file detected: {event.src_path}")
            # Wait a bit to ensure file is fully written
            time.sleep(self.config.get('post_delay', 2))
            self.post_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification event"""
        if not event.is_directory and self.config.get('post_on_modify', False):
            logger.debug(f"File modified: {event.src_path}")
            time.sleep(self.config.get('post_delay', 2))
            self.post_file(event.src_path)


class UsenetSync:
    """Main UsenetSync application"""
    
    def __init__(self, config_file='usenet_sync_config.json'):
        self.config = self.load_config(config_file)
        self.client = None
        self.observer = None
        self.handler = None
    
    def load_config(self, config_file):
        """Load application configuration"""
        default_config = {
            'watch_directories': ['./upload'],
            'allowed_extensions': [],  # Empty = all files
            'min_file_size': 0,
            'max_file_size': 0,  # 0 = no limit
            'default_newsgroup': 'alt.binaries.test',
            'newsgroup_map': {
                '*.zip': 'alt.binaries.test',
                '*.rar': 'alt.binaries.test',
                '*.mp3': 'alt.binaries.sounds.mp3',
                '*.jpg': 'alt.binaries.pictures',
                '*.png': 'alt.binaries.pictures'
            },
            'subject_template': '{filename} - {size}',
            'from_user': 'usenet-sync@auto.post',
            'post_delay': 2,
            'post_on_modify': False,
            'posted_files_log': 'posted_files.json',
            'posting_log': 'posting_history.log',
            'scan_existing': True
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config: {config_path}")
        
        return default_config
    
    def setup(self):
        """Setup NNTP client and file watcher"""
        try:
            # Create NNTP client
            logger.info("Connecting to NNTP server...")
            self.client = ProductionNNTPClient.from_config()
            logger.info(f"[OK] Connected to {self.client.host}")
            
            # Create handler
            self.handler = UsenetSyncHandler(self.client, self.config)
            
            # Create observer
            self.observer = Observer()
            
            # Add watch directories
            for directory in self.config['watch_directories']:
                dir_path = Path(directory)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True)
                    logger.info(f"Created watch directory: {dir_path}")
                
                self.observer.schedule(self.handler, str(dir_path), recursive=True)
                logger.info(f"Watching directory: {dir_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            logger.exception("Setup exception")
            return False
    
    def scan_existing_files(self):
        """Scan and post existing files in watch directories"""
        if not self.config.get('scan_existing', True):
            return
        
        logger.info("Scanning existing files...")
        
        total_files = 0
        posted_files = 0
        
        for directory in self.config['watch_directories']:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    if self.handler.post_file(file_path):
                        posted_files += 1
        
        logger.info(f"Scan complete: posted {posted_files}/{total_files} files")
    
    def run(self):
        """Run the file watcher"""
        if not self.setup():
            return False
        
        try:
            # Scan existing files
            self.scan_existing_files()
            
            # Start watching
            self.observer.start()
            logger.info("UsenetSync is running. Press Ctrl+C to stop.")
            
            # Keep running
            while True:
                time.sleep(1)
                
                # Periodic stats
                if int(time.time()) % 60 == 0:
                    stats = self.client.get_stats()
                    logger.info(f"Stats - Posts: {stats['posts_successful']}, "
                              f"Failed: {stats['posts_failed']}, "
                              f"Rate: {stats['success_rate']:.1%}")
                
        except KeyboardInterrupt:
            logger.info("Stopping UsenetSync...")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
            logger.exception("Runtime exception")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")
        
        if self.client:
            self.client.close()
            logger.info("NNTP connections closed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UsenetSync - Automatic Usenet Poster')
    parser.add_argument('--config', default='usenet_sync_config.json', help='Configuration file')
    parser.add_argument('--test', action='store_true', help='Run integration test')
    
    args = parser.parse_args()
    
    if args.test:
        # Run integration test
        print("Running integration test...")
        os.system(f"{sys.executable} integration_test_real.py")
    else:
        # Run main application
        app = UsenetSync(args.config)
        app.run()


if __name__ == "__main__":
    main()
