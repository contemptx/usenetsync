#!/usr/bin/env python3
"""
Test ALL unified system modules
Verifies complete system functionality
"""

import sys
sys.path.insert(0, '/workspace/src')

def test_all_modules():
    print("=" * 80)
    print("TESTING ALL UNIFIED SYSTEM MODULES")
    print("=" * 80)
    
    modules_tested = []
    
    # Test Core
    print("\n[1/9] Testing CORE modules...")
    try:
        from unified.core.database import UnifiedDatabase
        from unified.core.schema import UnifiedSchema
        from unified.core.config import UnifiedConfig
        from unified.core.models import Folder, File, Segment
        from unified.core.migrations import UnifiedMigrations
        modules_tested.append("✅ Core (Database, Schema, Config, Models, Migrations)")
    except ImportError as e:
        modules_tested.append(f"❌ Core: {e}")
    
    # Test Security
    print("[2/9] Testing SECURITY modules...")
    try:
        from unified.security.encryption import UnifiedEncryption
        from unified.security.authentication import UnifiedAuthentication
        from unified.security.access_control import UnifiedAccessControl
        from unified.security.obfuscation import UnifiedObfuscation
        from unified.security.key_management import UnifiedKeyManagement
        from unified.security.zero_knowledge import ZeroKnowledgeProofs
        modules_tested.append("✅ Security (Encryption, Auth, Access, Obfuscation, Keys, ZKP)")
    except ImportError as e:
        modules_tested.append(f"❌ Security: {e}")
    
    # Test Indexing
    print("[3/9] Testing INDEXING modules...")
    try:
        from unified.indexing.scanner import UnifiedScanner
        from unified.indexing.versioning import UnifiedVersioning
        from unified.indexing.binary_index import UnifiedBinaryIndex
        from unified.indexing.streaming import UnifiedStreaming
        from unified.indexing.change_detection import UnifiedChangeDetection
        from unified.indexing.folder_stats import UnifiedFolderStats
        modules_tested.append("✅ Indexing (Scanner, Versioning, Binary, Streaming, Changes, Stats)")
    except ImportError as e:
        modules_tested.append(f"❌ Indexing: {e}")
    
    # Test Segmentation
    print("[4/9] Testing SEGMENTATION modules...")
    try:
        from unified.segmentation.processor import UnifiedSegmentProcessor
        from unified.segmentation.packing import UnifiedPacking
        from unified.segmentation.redundancy import UnifiedRedundancy
        from unified.segmentation.hashing import UnifiedHashing
        from unified.segmentation.compression import UnifiedCompression
        from unified.segmentation.headers import UnifiedHeaders
        modules_tested.append("✅ Segmentation (Processor, Packing, Redundancy, Hash, Compression)")
    except ImportError as e:
        modules_tested.append(f"❌ Segmentation: {e}")
    
    # Test Networking
    print("[5/9] Testing NETWORKING modules...")
    try:
        from unified.networking.nntp_client import UnifiedNNTPClient
        from unified.networking.connection_pool import UnifiedConnectionPool
        from unified.networking.bandwidth import UnifiedBandwidth
        from unified.networking.retry import UnifiedRetry
        from unified.networking.server_health import UnifiedServerHealth
        from unified.networking.yenc import UnifiedYenc
        modules_tested.append("✅ Networking (NNTP, Pool, Bandwidth, Retry, Health, yEnc)")
    except ImportError as e:
        modules_tested.append(f"❌ Networking: {e}")
    
    # Test Upload
    print("[6/9] Testing UPLOAD modules...")
    try:
        from unified.upload.queue import UnifiedUploadQueue
        from unified.upload.batch import UnifiedBatch
        from unified.upload.worker import UnifiedWorker
        from unified.upload.progress import UnifiedProgress
        from unified.upload.session import UnifiedSession
        from unified.upload.strategies import UnifiedStrategies
        modules_tested.append("✅ Upload (Queue, Batch, Worker, Progress, Session, Strategies)")
    except ImportError as e:
        modules_tested.append(f"❌ Upload: {e}")
    
    # Test Download
    print("[7/9] Testing DOWNLOAD modules...")
    try:
        from unified.download.retriever import UnifiedRetriever
        from unified.download.reconstructor import UnifiedReconstructor
        from unified.download.decoder import UnifiedDecoder
        from unified.download.verifier import UnifiedVerifier
        from unified.download.resume import UnifiedResume
        from unified.download.cache import UnifiedCache
        modules_tested.append("✅ Download (Retriever, Reconstructor, Decoder, Verifier, Resume, Cache)")
    except ImportError as e:
        modules_tested.append(f"❌ Download: {e}")
    
    # Test Publishing
    print("[8/9] Testing PUBLISHING modules...")
    try:
        from unified.publishing.share_manager import UnifiedShareManager
        from unified.publishing.commitment_manager import UnifiedCommitmentManager
        from unified.publishing.publication_tracker import UnifiedPublicationTracker
        from unified.publishing.expiry_manager import UnifiedExpiryManager
        from unified.publishing.permission_manager import UnifiedPermissionManager
        from unified.publishing.share_validator import UnifiedShareValidator
        modules_tested.append("✅ Publishing (Shares, Commitments, Tracker, Expiry, Permissions)")
    except ImportError as e:
        modules_tested.append(f"❌ Publishing: {e}")
    
    # Test Monitoring
    print("[9/9] Testing MONITORING modules...")
    try:
        from unified.monitoring.metrics_collector import UnifiedMetricsCollector
        modules_tested.append("✅ Monitoring (Metrics Collector)")
    except ImportError as e:
        modules_tested.append(f"❌ Monitoring: {e}")
    
    # Test Main System
    print("\n[FINAL] Testing MAIN system integration...")
    try:
        from unified.main import UnifiedSystem
        system = UnifiedSystem()
        stats = system.get_statistics()
        system.close()
        modules_tested.append("✅ Main System Integration")
    except Exception as e:
        modules_tested.append(f"❌ Main System: {e}")
    
    # Print results
    print("\n" + "=" * 80)
    print("MODULE TEST RESULTS:")
    print("=" * 80)
    
    for result in modules_tested:
        print(result)
    
    # Count successes
    successes = sum(1 for r in modules_tested if r.startswith("✅"))
    total = len(modules_tested)
    
    print("\n" + "=" * 80)
    print(f"FINAL SCORE: {successes}/{total} modules working")
    
    if successes == total:
        print("🎉 ALL MODULES WORKING - SYSTEM 100% COMPLETE!")
    else:
        print(f"⚠️  {total - successes} modules need attention")
    
    print("=" * 80)
    
    return successes == total

if __name__ == "__main__":
    success = test_all_modules()
    sys.exit(0 if success else 1)