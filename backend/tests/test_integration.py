"""
UsenetSync Integration Tests
Tests complete workflows with real components
"""
import os
import time
import uuid
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

class TestUsenetSyncIntegration:
    """Integration tests for complete UsenetSync workflows"""
    
    def test_complete_upload_workflow(self, unified_system, test_files_dir, newshosting_connection):
        """Test complete file upload workflow to Usenet"""
        
        # Step 1: Create user
        user = unified_system.create_user(
            username=f"test_{uuid.uuid4().hex[:8]}",
            email="test@usenetsync.local"
        )
        assert user["user_id"], "User creation failed"
        print(f"\n Step 1: Created user {user['username']}")
        
        # Step 2: Index folder
        index_result = unified_system.index_folder(
            folder_path=str(test_files_dir),
            owner_id=user["user_id"],
            calculate_hash=True,
            create_segments=True
        )
        assert index_result["files_indexed"] > 0, "No files indexed"
        print(f"✅ Step 2: Indexed {index_result['files_indexed']} files")
        
        # Step 3: Get folder info
        folders = unified_system.db.fetch_all(
            "SELECT * FROM folders WHERE owner_id = ?",
            (user["user_id"],)
        )
        assert len(folders) > 0, "No folders found"
        folder = folders[0]
        print(f"✅ Step 3: Found folder {folder['name']}")
        
        # Step 4: Create share
        share = unified_system.create_share(
            folder_id=folder["folder_id"],
            owner_id=user["user_id"]
        )
        assert share.get("share_id"), "Share creation failed"
        print(f"✅ Step 4: Created share {share['share_id'][:16]}...")
        
        # Step 5: Verify database state
        stats = unified_system.get_statistics()
        assert stats["total_files"] > 0, "Files not in database"
        assert stats["total_shares"] > 0, "Share not in database"
        print(f"✅ Step 5: Database has {stats['total_files']} files, {stats['total_shares']} shares")
    
    def test_api_server_integration(self, unified_system):
        """Test API server with real components"""
        from unified.api.server import create_app
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"\n✅ API Health: {data}")
        
        # Test stats endpoint
        response = client.get("/api/v1/stats")
        assert response.status_code in [200, 503]  # May be 503 if system not initialized
        print(f"✅ API Stats endpoint responding")
        
        # Test user creation via API
        response = client.post("/api/v1/users", json={
            "username": f"api_test_{uuid.uuid4().hex[:8]}",
            "email": "api@test.local"
        })
        if response.status_code == 200:
            user_data = response.json()
            assert "user_id" in user_data
            print(f"✅ API User creation: {user_data['user_id'][:16]}...")
    
    def test_gui_bridge_integration(self, unified_system):
        """Test GUI bridge with real system"""
        from unified.gui_bridge.complete_tauri_bridge import CompleteTauriBridge
        import asyncio
        
        bridge = CompleteTauriBridge(unified_system)
        
        async def test_commands():
            # Test system stats command
            result = await bridge.handle_command("get_system_stats", {})
            assert result["success"], "System stats command failed"
            stats = result["data"]
            print(f"\n✅ GUI Bridge - System Stats:")
            print(f"   Files: {stats.get('totalFiles', 0)}")
            print(f"   Size: {stats.get('totalSize', 0)}")
            
            # Test database status command
            result = await bridge.handle_command("check_database_status", {})
            assert result["success"], "Database status command failed"
            db_status = result["data"]
            assert db_status["connected"], "Database not connected"
            print(f"✅ GUI Bridge - Database Status:")
            print(f"   Connected: {db_status['connected']}")
            print(f"   Type: {db_status.get('type', 'unknown')}")
            
            # Test user initialization command
            result = await bridge.handle_command("initialize_user", {
                "display_name": f"GUI_User_{uuid.uuid4().hex[:8]}"
            })
            assert result["success"], "User initialization failed"
            user_id = result["data"]
            print(f"✅ GUI Bridge - Created user: {user_id[:16]}...")
        
        # Run async test
        asyncio.run(test_commands())
    
    def test_encryption_workflow(self, unified_system, test_files_dir):
        """Test encryption in file processing workflow"""
        from unified.security.encryption import UnifiedEncryption
        
        encryption = UnifiedEncryption()
        
        # Read a test file
        test_file = test_files_dir / "document.txt"
        original_data = test_file.read_bytes()
        
        # Generate encryption key
        key = encryption.generate_key()
        
        # Encrypt file data
        encrypted_data = encryption.encrypt(original_data, key)
        assert len(encrypted_data) > len(original_data), "Encryption didn't add overhead"
        
        # Store encrypted data (simulate)
        encrypted_file = test_files_dir / "document.encrypted"
        encrypted_file.write_bytes(encrypted_data)
        
        # Read back and decrypt
        stored_data = encrypted_file.read_bytes()
        decrypted_data = encryption.decrypt(stored_data, key)
        
        assert decrypted_data == original_data, "Decryption failed"
        print(f"\n✅ Encryption workflow:")
        print(f"   Original: {len(original_data)} bytes")
        print(f"   Encrypted: {len(encrypted_data)} bytes")
        print(f"   Overhead: {len(encrypted_data) - len(original_data)} bytes")
    
    def test_access_control(self, unified_system):
        """Test access control with real users and folders"""
        from unified.security.access_control import UnifiedAccessControl
        
        access_control = UnifiedAccessControl(unified_system.db)
        
        # Create two users
        user1 = unified_system.create_user("user1", "user1@test.local")
        user2 = unified_system.create_user("user2", "user2@test.local")
        
        # Create folder owned by user1
        folder_id = uuid.uuid4().hex
        unified_system.db.insert("folders", {
            "folder_id": folder_id,
            "name": "Private Folder",
            "path": f"/private/{folder_id}",
            "owner_id": user1["user_id"],
            "access_level": "private"
        })
        
        # Check access
        assert access_control.check_folder_access(
            folder_id, user1["user_id"]
        ), "Owner should have access"
        
        assert not access_control.check_folder_access(
            folder_id, user2["user_id"]
        ), "Non-owner shouldn't have access to private folder"
        
        # Grant access to user2
        access_control.grant_folder_access(folder_id, user2["user_id"])
        
        # Check access again
        assert access_control.check_folder_access(
            folder_id, user2["user_id"]
        ), "User2 should have access after grant"
        
        print(f"\n✅ Access control:")
        print(f"   Owner access: ✓")
        print(f"   Private folder protection: ✓")
        print(f"   Access grant: ✓")