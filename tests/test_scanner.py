import pytest
from gencodedoc.core.scanner import FileScanner

def test_scan_files(config_manager, temp_project):
    config = config_manager.init_project()
    scanner = FileScanner(config)
    
    files = scanner.scan()
    assert len(files) >= 2  # main.py, README.md
    
    paths = [f.path for f in files]
    assert "src/main.py" in paths
    assert "README.md" in paths

def test_ignore_rules(config_manager, temp_project):
    config = config_manager.init_project()
    
    # Create ignored file
    (temp_project / ".env").write_text("SECRET=123")
    config.ignore.files.append(".env")
    config_manager.save(config)
    
    scanner = FileScanner(config)
    files = scanner.scan()
    
    paths = [f.path for f in files]
    assert ".env" not in paths
