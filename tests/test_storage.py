import pytest
from gencodedoc.storage.snapshot_store import SnapshotStore
from gencodedoc.models.snapshot import FileEntry
import hashlib

def test_store_initialization(temp_project):
    store = SnapshotStore(temp_project / ".store", temp_project)
    assert (temp_project / ".store" / "gencodedoc.db").exists()

def test_deduplication(temp_project, config_manager):
    config = config_manager.init_project()
    store = SnapshotStore(temp_project / ".gencodedoc", temp_project)
    
    content = b"duplicate content"
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Store first time
    store.db.store_content(file_hash, content, len(content), len(content))
    assert store.db.content_exists(file_hash)
    
    # Store second time (should verify existence)
    assert store.db.content_exists(file_hash)

def test_compression(temp_project, config_manager):
    config = config_manager.init_project()
    config.compression_enabled = True
    
    store = SnapshotStore(
        temp_project / ".gencodedoc", 
        temp_project, 
        compression_enabled=True
    )
    
    # Create file
    file_path = temp_project / "large_file.txt"
    file_path.write_text("A" * 1000)
    
    # Mocking behavior (SnapshotStore handles logic internally during create_snapshot)
    # Here we test if compressor works
    compressed, orig, comp = store.compressor.compress_file(str(file_path))
    assert comp < orig
