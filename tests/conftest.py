import pytest
import shutil
from pathlib import Path
from gencodedoc.core.config import ConfigManager
from gencodedoc.core.versioning import VersionManager
from gencodedoc.storage.database import Database
from gencodedoc.storage.snapshot_store import SnapshotStore

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project environment"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create some dummy files
    (project_dir / "src").mkdir()
    (project_dir / "src/main.py").write_text("print('hello')")
    (project_dir / "README.md").write_text("# Test Project")
    
    yield project_dir
    
    # Cleanup (handled by tmp_path but good practice)
    if project_dir.exists():
        shutil.rmtree(project_dir)

@pytest.fixture
def config_manager(temp_project):
    """Initialize ConfigManager"""
    return ConfigManager(temp_project)

@pytest.fixture
def version_manager(temp_project, config_manager):
    """Initialize VersionManager"""
    # Create config first
    config_manager.init_project()
    config = config_manager.load()
    return VersionManager(config)

@pytest.fixture
def mock_db(temp_project):
    """Initialize a test database"""
    db_path = temp_project / ".gencodedoc" / "gencodedoc.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return Database(db_path)
