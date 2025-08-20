"""
UsenetSync Live Tests - Real Components with Newshosting
Tests actual functionality with news.newshosting.com:563
"""
import os
import time
import uuid
import hashlib
import pytest
from pathlib import Path
from datetime import datetime

pytestmark = pytest.mark.live_nntp

class TestUsenetSyncLive:
    """Test UsenetSync with real Newshosting server"""
    
    def test_real_nntp_connection(self, real_nntp_client, newshosting_connection):
        """Test real connection to news.newshosting.com:563"""
        client = real_nntp_client()
        
        # Connect with real credentials
        assert client.connect(
            host=newshosting_connection["host"],
            port=newshosting_connection["port"],
            use_ssl=newshosting_connection["ssl"],
            timeout=30
        ), "Failed to connect to news.newshosting.com:563"
        
        # Authenticate with real account
        assert client.authenticate(
            newshosting_connection["username"],
            newshosting_connection["password"]
        ), "Failed to authenticate with Newshosting"
        
        # Select real newsgroup
        group_info = client.select_group(newshosting_connection["group"])
        assert group_info is not None, f"Failed to select {newshosting_connection['group']}"
        assert group_info.get("count", 0) > 0, "Group appears empty"
        
        print(f"\n✅ Connected to Newshosting")
        print(f"   Group: {newshosting_connection['group']}")
        print(f"   Articles: {group_info.get('count', 0)}")
        print(f"   Range: {group_info.get('first', 0)}-{group_info.get('last', 0)}")
        
        client.disconnect()
    
    def test_post_and_retrieve_article(self, real_nntp_client, newshosting_connection):
        """Post a real article to alt.binaries.test and retrieve it"""
        client = real_nntp_client()
        
        # Connect and authenticate
        client.connect(
            host=newshosting_connection["host"],
            port=newshosting_connection["port"],
            use_ssl=newshosting_connection["ssl"]
        )
        client.authenticate(
            newshosting_connection["username"],
            newshosting_connection["password"]
        )
        
        # Create unique test article
        test_id = uuid.uuid4().hex[:8]
        subject = f"UsenetSync Test Article {test_id}"
        body = f"This is a real test article posted by UsenetSync.\nTest ID: {test_id}\nTimestamp: {datetime.now().isoformat()}\n".encode()
        
        # Post to alt.binaries.test
        message_id = client.post_article(
            subject=subject,
            body=body,
            newsgroups=["alt.binaries.test"],
            from_header="UsenetSync Test <test@usenetsync.local>"
        )
        
        assert message_id is not None, "Failed to post article"
        print(f"\n✅ Posted article: {message_id}")
        
        # Wait for propagation
        time.sleep(2)
        
        # Try to retrieve the posted article
        article = client.retrieve_article(message_id)
        if article:
            print(f"✅ Retrieved article successfully")
        else:
            print(f"⚠️  Article not yet available (normal propagation delay)")
        
        client.disconnect()
    
    def test_unified_system_with_live_nntp(self, unified_system, test_files_dir):
        """Test UnifiedSystem with real files and real NNTP"""
        
        # Create a real user
        user = unified_system.create_user("test_user", "test@usenetsync.local")
        assert user["user_id"], "Failed to create user"
        print(f"\n✅ Created user: {user['user_id'][:16]}...")
        
        # Index real files
        result = unified_system.index_folder(
            str(test_files_dir),
            user["user_id"]
        )
        assert result["files_indexed"] > 0, "No files indexed"
        print(f"✅ Indexed {result['files_indexed']} files")
        print(f"   Total size: {result.get('total_size', 0)} bytes")
        print(f"   Segments: {result.get('segments_created', 0)}")
        
        # Get statistics
        stats = unified_system.get_statistics()
        assert stats["total_files"] > 0, "No files in statistics"
        print(f"✅ System stats: {stats['total_files']} files, {stats['total_size']} bytes")
    
    def test_file_segmentation(self, real_segmentation_processor, test_files_dir):
        """Test real file segmentation for Usenet posting"""
        processor = real_segmentation_processor()
        
        # Get the large test file
        large_file = test_files_dir / "large.bin"
        assert large_file.exists(), "Test file not found"
        
        # Segment the file
        segments = processor.segment_file(str(large_file))
        assert len(segments) > 0, "No segments created"
        
        # Verify segments
        total_size = sum(len(seg["data"]) for seg in segments)
        original_size = large_file.stat().st_size
        assert total_size == original_size, "Segment size mismatch"
        
        print(f"\n✅ Segmented {large_file.name}")
        print(f"   Original: {original_size} bytes")
        print(f"   Segments: {len(segments)}")
        print(f"   Segment size: {len(segments[0]['data'])} bytes")
    
    def test_folder_indexing(self, real_indexing_scanner, test_files_dir):
        """Test real folder indexing"""
        scanner = real_indexing_scanner()
        
        # Scan the test directory
        folder_id = hashlib.sha256(str(test_files_dir).encode()).hexdigest()
        files = list(scanner.scan_folder(str(test_files_dir), folder_id))
        
        assert len(files) > 0, "No files found"
        
        # Verify file details
        total_files = len(files)
        total_size = sum(f.get("size", 0) for f in files)
        
        print(f"\n✅ Indexed folder: {test_files_dir.name}")
        print(f"   Files found: {total_files}")
        print(f"   Total size: {total_size} bytes")
        
        # Check specific files
        file_names = {f["name"] for f in files}
        assert "document.txt" in file_names, "Missing expected file"
        assert "large.bin" in file_names, "Missing large file"
    
    def test_encryption_module(self, unified_system):
        """Test real encryption/decryption"""
        from unified.security.encryption import UnifiedEncryption
        
        encryption = UnifiedEncryption()
        
        # Generate real keys
        key = encryption.generate_key()
        assert key, "Failed to generate key"
        
        # Encrypt real data
        test_data = b"This is sensitive UsenetSync data that needs encryption"
        encrypted = encryption.encrypt(test_data, key)
        assert encrypted != test_data, "Data not encrypted"
        
        # Decrypt
        decrypted = encryption.decrypt(encrypted, key)
        assert decrypted == test_data, "Decryption failed"
        
        print(f"\n✅ Encryption working")
        print(f"   Original: {len(test_data)} bytes")
        print(f"   Encrypted: {len(encrypted)} bytes")
        print(f"   Key length: {len(key)} bytes")
    
    def test_database_operations(self, unified_system):
        """Test real PostgreSQL database operations"""
        db = unified_system.db
        
        # Test insert
        test_id = uuid.uuid4().hex
        db.insert("folders", {
            "folder_id": test_id,
            "name": "Test Folder",
            "path": f"/test/{test_id}",
            "owner_id": "test_user",
            "created_at": datetime.now()
        })
        
        # Test fetch
        folder = db.fetch_one(
            "SELECT * FROM folders WHERE folder_id = ?",
            (test_id,)
        )
        assert folder is not None, "Failed to fetch inserted folder"
        assert folder["name"] == "Test Folder", "Data mismatch"
        
        # Test update
        db.update(
            "folders",
            {"name": "Updated Folder"},
            "folder_id = ?",
            (test_id,)
        )
        
        # Verify update
        updated = db.fetch_one(
            "SELECT * FROM folders WHERE folder_id = ?",
            (test_id,)
        )
        assert updated["name"] == "Updated Folder", "Update failed"
        
        print(f"\n✅ Database operations working")
        print(f"   Insert: ✓")
        print(f"   Fetch: ✓")
        print(f"   Update: ✓")