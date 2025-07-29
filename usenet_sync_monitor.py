# Fix Windows console encoding
import sys
import io
if sys.platform == 'win32':
    # Set console encoding to UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


﻿#!/usr/bin/env python3
"""
Real-time monitor for UsenetSync activity
Shows live statistics and posting activity
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class UsenetSyncMonitor:
    def __init__(self):
        self.last_history_size = 0
        self.start_time = time.time()
    
    def get_posted_files(self):
        """Get posted files list"""
        posted_file = Path("posted_files.json")
        if posted_file.exists():
            with open(posted_file, 'r') as f:
                return json.load(f)
        return []
    
    def get_posting_history(self):
        """Get posting history"""
        history_file = Path("posting_history.log")
        if history_file.exists():
            with open(history_file, 'r') as f:
                lines = f.readlines()
            
            history = []
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    history.append({
                        'timestamp': parts[0],
                        'file': parts[1],
                        'newsgroup': parts[2],
                        'message_id': parts[3],
                        'post_time': float(parts[4])
                    })
            return history
        return []
    
    def get_upload_directory_status(self):
        """Get status of upload directory"""
        upload_dir = Path("upload")
        if upload_dir.exists():
            files = list(upload_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            return {
                'file_count': len([f for f in files if f.is_file()]),
                'total_size': total_size,
                'files': [f.name for f in files if f.is_file()]
            }
        return {'file_count': 0, 'total_size': 0, 'files': []}
    
    def get_nntp_stats(self):
        """Try to get NNTP client statistics"""
        # This would need to be implemented to read from a stats file
        # For now, calculate from history
        history = self.get_posting_history()
        if history:
            total_posts = len(history)
            total_time = sum(h['post_time'] for h in history)
            avg_time = total_time / total_posts if total_posts > 0 else 0
            
            # Calculate success rate (all logged posts are successful)
            return {
                'total_posts': total_posts,
                'success_rate': 100.0,
                'average_post_time': avg_time
            }
        return {
            'total_posts': 0,
            'success_rate': 0.0,
            'average_post_time': 0.0
        }
    
    def display_dashboard(self):
        """Display monitoring dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("╔" + "═"*58 + "╗")
        print("║" + " USENET SYNC MONITOR ".center(58) + "║")
        print("╠" + "═"*58 + "╣")
        
        # Upload directory status
        upload_status = self.get_upload_directory_status()
        print("║ Upload Directory:".ljust(59) + "║")
        print(f"║   Files waiting: {upload_status['file_count']}".ljust(59) + "║")
        print(f"║   Total size: {upload_status['total_size']:,} bytes".ljust(59) + "║")
        
        # Posted files
        posted_files = self.get_posted_files()
        print("╠" + "═"*58 + "╣")
        print("║ Posted Files:".ljust(59) + "║")
        print(f"║   Total posted: {len(posted_files)}".ljust(59) + "║")
        
        # NNTP Statistics
        stats = self.get_nntp_stats()
        print("╠" + "═"*58 + "╣")
        print("║ NNTP Statistics:".ljust(59) + "║")
        print(f"║   Total posts: {stats['total_posts']}".ljust(59) + "║")
        print(f"║   Success rate: {stats['success_rate']:.1f}%".ljust(59) + "║")
        print(f"║   Avg post time: {stats['average_post_time']:.2f}s".ljust(59) + "║")
        
        # Recent activity
        history = self.get_posting_history()
        print("╠" + "═"*58 + "╣")
        print("║ Recent Posts:".ljust(59) + "║")
        
        if history:
            for post in history[-5:]:  # Last 5 posts
                timestamp = post['timestamp'].split('T')[1].split('.')[0]
                filename = os.path.basename(post['file'])[:30]
                print(f"║   {timestamp} {filename:<30} {post['post_time']:.1f}s".ljust(59) + "║")
        else:
            print("║   No posts yet".ljust(59) + "║")
        
        # Runtime
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        seconds = int(runtime % 60)
        
        print("╠" + "═"*58 + "╣")
        print(f"║ Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}".ljust(59) + "║")
        print("║ Press Ctrl+C to exit".ljust(59) + "║")
        print("╚" + "═"*58 + "╝")
        
        # Check for new posts
        current_history_size = len(history)
        if current_history_size > self.last_history_size:
            new_posts = current_history_size - self.last_history_size
            print(f"\n🔔 {new_posts} new post(s) detected!")
            self.last_history_size = current_history_size
    
    def run(self):
        """Run the monitor"""
        print("Starting UsenetSync Monitor...")
        print("This will refresh every 5 seconds.")
        print("Press Ctrl+C to exit.\n")
        
        try:
            while True:
                self.display_dashboard()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nMonitor stopped.")
            

def main():
    monitor = UsenetSyncMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
