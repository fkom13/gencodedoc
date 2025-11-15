"""Tests for versioning system"""
import pytest
from pathlib import Path
from gencodedoc.core.versioning import VersionManager
from gencodedoc.models.config import ProjectConfig


def test_version_manager_initialization(tmp_path):
    """Test version manager initialization"""
    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)

    assert vm.config == config
    assert vm.scanner is not None
    assert vm.store is not None


def test_create_snapshot(tmp_path):
    """Test snapshot creation"""
    # Create test files
    (tmp_path / "test.txt").write_text("Hello")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)

    snapshot = vm.create_snapshot(message="Test snapshot")

    assert snapshot.metadata.id is not None
    assert snapshot.metadata.message == "Test snapshot"
    assert snapshot.metadata.files_count > 0


def test_list_snapshots(tmp_path):
    """Test snapshot listing"""
    (tmp_path / "test.txt").write_text("Hello")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)

    # Create first snapshot
    vm.create_snapshot(message="Snapshot 1")
    
    # Modify file to get different hash
    (tmp_path / "test.txt").write_text("Hello World - Modified")
    
    # Create second snapshot
    vm.create_snapshot(message="Snapshot 2")

    snapshots = vm.list_snapshots()

    assert len(snapshots) == 2


def test_snapshot_with_tag(tmp_path):
    """Test snapshot with tag"""
    (tmp_path / "test.txt").write_text("Hello")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)

    snapshot = vm.create_snapshot(message="Tagged", tag="v1.0")

    # Retrieve by tag
    retrieved = vm.get_snapshot("v1.0")

    assert retrieved is not None
    assert retrieved.metadata.tag == "v1.0"


def test_diff_snapshots(tmp_path):
    """Test snapshot diffing"""
    # Create initial file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Version 1")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)

    # First snapshot
    snap1 = vm.create_snapshot(message="Version 1")

    # Modify file
    test_file.write_text("Version 2 - Changed content")

    # Second snapshot
    snap2 = vm.create_snapshot(message="Version 2")

    # Calculate diff
    diff = vm.diff_snapshots(str(snap1.metadata.id), str(snap2.metadata.id))

    assert diff.total_changes > 0
    assert len(diff.files_modified) > 0
