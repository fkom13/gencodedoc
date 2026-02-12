import pytest
from gencodedoc.mcp.tools import execute_tool, get_tools_definition

def test_get_tools():
    tools = get_tools_definition()
    names = [t["name"] for t in tools]
    assert "create_snapshot" in names
    assert "get_config" in names
    assert "start_autosave" in names

def test_execute_list_snapshots(version_manager, config_manager):
    # Setup
    config = config_manager.load()
    
    # Execute
    result = execute_tool(
        "list_snapshots", 
        {}, 
        version_manager, 
        None, 
        config
    )
    
    # Assert
    assert "snapshots" in result
    assert result["count"] == 0

def test_execute_create_snapshot(version_manager, config_manager):
    # Setup
    config = config_manager.load()
    
    # Execute
    result = execute_tool(
        "create_snapshot", 
        {"message": "MCP Test", "tag": "mcp-v1"}, 
        version_manager, 
        None, 
        config
    )
    
    # Assert
    assert result["snapshot_id"] is not None
    assert result["tag"] == "mcp-v1"

def test_execute_restore_files(version_manager, config_manager, temp_project):
    config = config_manager.load()
    (temp_project / "file1.txt").write_text("v1")
    version_manager.create_snapshot(tag="v1")
    (temp_project / "file1.txt").write_text("v2")
    
    result = execute_tool(
        "restore_files",
        {
            "snapshot_ref": "v1",
            "file_filters": ["file1.txt"]
        },
        version_manager, None, config
    )
    assert result["success"] is True
    assert (temp_project / "file1.txt").read_text() == "v1"

def test_execute_get_file_at_version(version_manager, config_manager, temp_project):
    config = config_manager.load()
    (temp_project / "src/main.py").write_text("v1")
    version_manager.create_snapshot(tag="v1")
    
    result = execute_tool(
        "get_file_at_version",
        {"snapshot_ref": "v1", "file_path": "src/main.py"},
        version_manager, None, config
    )
    assert "content" in result
    assert "v1" in result["content"][0]["text"]

def test_set_config_value(version_manager, config_manager):
    config = config_manager.load()
    
    result = execute_tool(
        "set_config_value",
        {"key": "autosave.enabled", "value": True},
        version_manager, None, config
    )
    
    assert result["key"] == "autosave.enabled"
    assert result["value"] is True
    
    # Reload to verify
    new_config = config_manager.load()
    assert new_config.autosave.enabled is True

