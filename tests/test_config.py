import pytest
from gencodedoc.core.config import ConfigManager
from pathlib import Path

def test_init_project(temp_project):
    manager = ConfigManager(temp_project)
    config = manager.init_project()
    
    assert config.project_name == temp_project.name
    assert (temp_project / ".gencodedoc.yaml").exists()

def test_load_config(temp_project):
    manager = ConfigManager(temp_project)
    manager.init_project()
    config = manager.load()
    
    assert config.project_path == temp_project.resolve()
    assert config.storage_path == Path(".gencodedoc")

def test_apply_python_preset(temp_project):
    manager = ConfigManager(temp_project)
    config = manager.init_project(preset="python")
    
    assert "venv" in config.ignore.dirs
    assert "__pycache__" in config.ignore.dirs
    assert ".pyc" in config.ignore.extensions

def test_apply_nodejs_preset(temp_project):
    manager = ConfigManager(temp_project)
    config = manager.init_project(preset="nodejs")
    
    assert "node_modules" in config.ignore.dirs
    assert "package-lock.json" in config.ignore.files

def test_save_config(temp_project):
    manager = ConfigManager(temp_project)
    config = manager.init_project()
    
    config.compression_enabled = False
    manager.save(config)
    
    loaded_config = manager.load()
    assert loaded_config.compression_enabled is False
