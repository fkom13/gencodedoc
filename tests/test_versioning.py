import pytest
from gencodedoc.core.versioning import VersionManager

def test_create_snapshot(version_manager):
    snapshot = version_manager.create_snapshot(message="Initial", tag="v1.0")
    
    assert snapshot.metadata.tag == "v1.0"
    assert snapshot.metadata.message == "Initial"
    assert snapshot.metadata.files_count > 0

def test_list_snapshots(version_manager, temp_project):
    version_manager.create_snapshot(tag="v1")
    
    # Modify project to create unique snapshot
    (temp_project / "new_file.txt").write_text("change")
    
    version_manager.create_snapshot(tag="v2")
    
    snapshots = version_manager.list_snapshots()
    assert len(snapshots) == 2
    assert snapshots[0].metadata.tag == "v2"  # Most recent first

def test_get_snapshot(version_manager):
    version_manager.create_snapshot(tag="v1")
    snapshot = version_manager.get_snapshot("v1")
    
    assert snapshot is not None
    assert snapshot.metadata.tag == "v1"

def test_restore_snapshot(version_manager, temp_project):
    # Snapshot functionality
    file_path = temp_project / "src/main.py"
    original_content = file_path.read_text()
    
    version_manager.create_snapshot(tag="v1")
    
    # Modify file
    file_path.write_text("print('modified')")
    
    # Restore
    version_manager.restore_snapshot("v1", force=True)
    
    assert file_path.read_text() == original_content

def test_partial_restore(version_manager, temp_project):
    # Create two files
    (temp_project / "file1.txt").write_text("v1")
    (temp_project / "file2.txt").write_text("v1")
    
    version_manager.create_snapshot(tag="v1")
    
    # Modify both
    (temp_project / "file1.txt").write_text("v2")
    (temp_project / "file2.txt").write_text("v2")
    
    # Restore only file1
    version_manager.restore_snapshot("v1", file_filters=["file1.txt"], force=True)
    
    assert (temp_project / "file1.txt").read_text() == "v1"
    assert (temp_project / "file2.txt").read_text() == "v2"
