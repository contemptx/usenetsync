#!/usr/bin/env python3
"""
Show Detailed Usenet Process with Real Data
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = "/workspace/backend/data/usenetsync.db"
REPORT_PATH = "/workspace/detailed_process_analysis.md"

def analyze_database():
    """Analyze the database and show detailed process information"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    report = []
    report.append("# 📊 DETAILED USENET PROCESS ANALYSIS")
    report.append("=" * 70)
    report.append(f"\nGenerated: {datetime.now().isoformat()}")
    report.append(f"Database: {DB_PATH}\n")
    
    # 1. FOLDER STRUCTURE
    report.append("\n## 📁 FOLDER STRUCTURE\n")
    cursor.execute("""
        SELECT folder_id, path, status, file_count, total_size, created_at
        FROM folders
        ORDER BY created_at DESC
        LIMIT 5
    """)
    folders = cursor.fetchall()
    
    if folders:
        report.append("### Recent Folders:\n")
        for folder in folders:
            folder_id, path, status, file_count, total_size, created = folder
            report.append(f"**Folder:** `{path}`")
            report.append(f"- ID: `{folder_id}`")
            report.append(f"- Status: {status}")
            report.append(f"- Files: {file_count}")
            report.append(f"- Size: {total_size:,} bytes" if total_size else "- Size: Unknown")
            report.append(f"- Created: {created}\n")
    
    # 2. INDEXED FILES
    report.append("\n## 🔍 INDEXED FILES\n")
    cursor.execute("""
        SELECT f.file_id, f.name, f.size, f.hash, f.mime_type, fo.path
        FROM files f
        JOIN folders fo ON f.folder_id = fo.folder_id
        ORDER BY f.created_at DESC
        LIMIT 10
    """)
    files = cursor.fetchall()
    
    if files:
        report.append("### Recent Files:\n")
        for file in files:
            file_id, name, size, hash_val, mime, folder_path = file
            report.append(f"**File:** `{name}`")
            report.append(f"- File ID: `{file_id}`")
            report.append(f"- Size: {size:,} bytes")
            report.append(f"- SHA256: `{hash_val[:32]}...`" if hash_val else "- SHA256: Not computed")
            report.append(f"- MIME: {mime}")
            report.append(f"- Folder: {folder_path}\n")
    else:
        report.append("*No indexed files found*\n")
    
    # 3. SEGMENTS
    report.append("\n## 📦 SEGMENTS\n")
    cursor.execute("""
        SELECT 
            f.name,
            COUNT(s.segment_id) as segment_count,
            MAX(s.total_segments) as total_segments,
            SUM(s.segment_size) as total_size,
            MIN(s.segment_hash) as first_hash
        FROM segments s
        JOIN files f ON s.file_id = f.file_id
        GROUP BY f.file_id
        ORDER BY f.name
        LIMIT 10
    """)
    segments = cursor.fetchall()
    
    if segments:
        report.append("### Segmented Files:\n")
        total_segments = 0
        for seg in segments:
            name, count, total, size, first_hash = seg
            total_segments += count
            report.append(f"**File:** `{name}`")
            report.append(f"- Segments: {count}/{total if total else count}")
            report.append(f"- Total Size: {size:,} bytes" if size else "- Total Size: Unknown")
            report.append(f"- First Segment Hash: `{first_hash[:24]}...`" if first_hash else "- No hash")
            report.append("")
        
        report.append(f"\n**Total Segments in Database:** {total_segments}\n")
        
        # Show sample segment details
        cursor.execute("""
            SELECT 
                s.segment_id,
                s.segment_number,
                s.segment_size,
                s.segment_hash,
                s.message_id,
                f.name
            FROM segments s
            JOIN files f ON s.file_id = f.file_id
            ORDER BY s.created_at DESC
            LIMIT 5
        """)
        sample_segments = cursor.fetchall()
        
        if sample_segments:
            report.append("### Sample Segment Details:\n")
            for seg in sample_segments:
                seg_id, seg_num, seg_size, seg_hash, msg_id, file_name = seg
                report.append(f"**Segment {seg_num} of {file_name}**")
                report.append(f"- Segment ID: `{seg_id}`")
                report.append(f"- Size: {seg_size:,} bytes")
                report.append(f"- Hash: `{seg_hash[:32]}...`" if seg_hash else "- Hash: Not computed")
                report.append(f"- Message ID: `{msg_id}`" if msg_id else "- Message ID: Not uploaded")
                report.append("")
    else:
        report.append("*No segments found*\n")
    
    # 4. MESSAGE IDS (from segments that have been uploaded)
    report.append("\n## 📨 MESSAGE IDS\n")
    cursor.execute("""
        SELECT DISTINCT message_id, segment_id, segment_number
        FROM segments
        WHERE message_id IS NOT NULL AND message_id != ''
        LIMIT 10
    """)
    message_ids = cursor.fetchall()
    
    if message_ids:
        report.append("### Uploaded Segments with Message IDs:\n")
        for msg_id, seg_id, seg_num in message_ids:
            report.append(f"- Message ID: `{msg_id}`")
            report.append(f"  - Segment: {seg_id} (#{seg_num})")
        report.append("")
    else:
        report.append("*No message IDs found (segments not uploaded to Usenet yet)*\n")
    
    # 5. SHARES
    report.append("\n## 🔗 SHARES\n")
    cursor.execute("""
        SELECT 
            s.share_id,
            s.access_level,
            s.created_at,
            s.download_count,
            f.path
        FROM shares s
        JOIN folders f ON s.folder_id = f.folder_id
        ORDER BY s.created_at DESC
        LIMIT 5
    """)
    shares = cursor.fetchall()
    
    if shares:
        report.append("### Recent Shares:\n")
        for share in shares:
            share_id, access, created, downloads, folder_path = share
            report.append(f"**Share ID:** `{share_id}`")
            report.append(f"- Access: {access}")
            report.append(f"- Downloads: {downloads}")
            report.append(f"- Created: {created}")
            report.append(f"- Folder: {folder_path}")
            report.append(f"- URL: `https://usenet-share.com/d/{share_id}`\n")
    else:
        report.append("*No shares found*\n")
    
    # 6. UPLOAD QUEUE
    report.append("\n## 📤 UPLOAD QUEUE\n")
    cursor.execute("""
        SELECT 
            uq.queue_id,
            uq.status,
            uq.priority,
            f.name,
            s.segment_number,
            s.segment_size
        FROM upload_queue uq
        JOIN segments s ON uq.segment_id = s.segment_id
        JOIN files f ON s.file_id = f.file_id
        ORDER BY uq.priority DESC, uq.created_at
        LIMIT 10
    """)
    queue = cursor.fetchall()
    
    if queue:
        report.append("### Upload Queue Status:\n")
        for item in queue:
            queue_id, status, priority, file_name, seg_num, seg_size = item
            report.append(f"- Queue #{queue_id}: {file_name} (Segment {seg_num})")
            report.append(f"  - Status: {status}")
            report.append(f"  - Priority: {priority}")
            report.append(f"  - Size: {seg_size:,} bytes")
        report.append("")
    else:
        report.append("*Upload queue is empty*\n")
    
    # 7. PROCESS SIMULATION
    report.append("\n## ⚙️ PROCESS SIMULATION\n")
    report.append("### How the Process Works:\n")
    report.append("1. **Indexing**: Files are scanned and metadata stored")
    report.append("   - File hash (SHA256) is calculated")
    report.append("   - MIME type is detected")
    report.append("   - File size and path are recorded\n")
    
    report.append("2. **Segmentation**: Large files are split into 700KB segments")
    report.append("   - Each segment gets a unique hash")
    report.append("   - Segment order is preserved")
    report.append("   - Metadata links segments to original files\n")
    
    report.append("3. **Upload to Usenet**: Segments are posted as articles")
    report.append("   - Each segment becomes a Usenet article")
    report.append("   - Server returns a unique Message-ID")
    report.append("   - Message-IDs are stored for retrieval\n")
    
    report.append("4. **Share Creation**: A unique share ID is generated")
    report.append("   - Contains references to all Message-IDs")
    report.append("   - Can be public, private, or protected")
    report.append("   - Share ID is all that's needed to download\n")
    
    report.append("5. **Download Process**: Using share ID to retrieve")
    report.append("   - Share ID maps to Message-IDs")
    report.append("   - Articles are downloaded from Usenet")
    report.append("   - Segments are reassembled in order")
    report.append("   - File hash is verified after reconstruction\n")
    
    # Example calculation
    report.append("### Example Timing (2.7 MB total):\n")
    report.append("```")
    report.append("Files: 3 (document.txt, image.jpg, video.mp4)")
    report.append("Total Size: 2,711,552 bytes")
    report.append("Segment Size: 700 KB")
    report.append("Total Segments: 4")
    report.append("")
    report.append("Indexing: ~0.3s (10 MB/s)")
    report.append("Segmentation: ~0.5s (8 segments/s)")
    report.append("Upload: ~2s (2 segments/s @ 1.4 MB/s)")
    report.append("Download: ~3s (1.3 segments/s)")
    report.append("Reconstruction: ~0.2s")
    report.append("Total: ~6 seconds")
    report.append("```\n")
    
    # Statistics
    report.append("\n## 📊 DATABASE STATISTICS\n")
    stats = {}
    for table in ['folders', 'files', 'segments', 'shares', 'upload_queue', 'download_queue']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        stats[table] = count
    
    report.append("### Record Counts:\n")
    for table, count in stats.items():
        report.append(f"- {table.capitalize()}: {count:,}")
    
    conn.close()
    
    # Write report
    report_text = "\n".join(report)
    with open(REPORT_PATH, "w") as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n📄 Report saved to: {REPORT_PATH}")

if __name__ == "__main__":
    analyze_database()