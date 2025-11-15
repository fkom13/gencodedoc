"""Tests for MCP server"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from gencodedoc.mcp.server import create_app
from gencodedoc.mcp.tools import get_tools_definition, execute_tool
from gencodedoc.models.config import ProjectConfig
from gencodedoc.core.versioning import VersionManager
from gencodedoc.core.documentation import DocumentationGenerator


def test_mcp_server_initialization(tmp_path):
    """Test MCP server initialization"""
    app = create_app(tmp_path)
    assert app is not None

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "GenCodeDoc MCP Server" in response.json()["name"]


def test_list_tools_endpoint(tmp_path):
    """Test tools listing endpoint"""
    app = create_app(tmp_path)
    client = TestClient(app)

    response = client.get("/mcp/tools")

    assert response.status_code == 200
    tools = response.json()["tools"]
    assert len(tools) > 0
    assert any(t["name"] == "create_snapshot" for t in tools)


def test_get_tools_definition():
    """Test tools definition structure"""
    tools = get_tools_definition()

    assert len(tools) > 0

    # Check create_snapshot tool
    create_snap = next(t for t in tools if t["name"] == "create_snapshot")
    assert "description" in create_snap
    assert "parameters" in create_snap


def test_create_snapshot_tool(tmp_path):
    """Test create_snapshot tool execution"""
    # Setup
    (tmp_path / "test.txt").write_text("Hello")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)
    doc_gen = DocumentationGenerator(config)

    # Execute tool
    result = execute_tool(
        tool_name="create_snapshot",
        parameters={"message": "Test snapshot"},
        version_manager=vm,
        doc_generator=doc_gen,
        config=config
    )

    assert result["snapshot_id"] is not None
    assert result["files_count"] > 0


def test_list_snapshots_tool(tmp_path):
    """Test list_snapshots tool"""
    (tmp_path / "test.txt").write_text("Hello")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)
    doc_gen = DocumentationGenerator(config)

    # Create snapshot first
    vm.create_snapshot(message="Test")

    # Execute tool
    result = execute_tool(
        tool_name="list_snapshots",
        parameters={"limit": 10},
        version_manager=vm,
        doc_generator=doc_gen,
        config=config
    )

    assert "snapshots" in result
    assert len(result["snapshots"]) > 0


def test_generate_documentation_tool(tmp_path):
    """Test generate_documentation tool"""
    (tmp_path / "test.py").write_text("print('test')")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)
    doc_gen = DocumentationGenerator(config)

    result = execute_tool(
        tool_name="generate_documentation",
        parameters={"include_tree": True, "include_code": True},
        version_manager=vm,
        doc_generator=doc_gen,
        config=config
    )

    assert "output_path" in result
    assert Path(result["output_path"]).exists()


def test_get_project_stats_tool(tmp_path):
    """Test get_project_stats tool"""
    (tmp_path / "test.py").write_text("print('test')")
    (tmp_path / "test.js").write_text("console.log('test')")

    config = ProjectConfig(project_path=tmp_path)
    vm = VersionManager(config)
    doc_gen = DocumentationGenerator(config)

    result = execute_tool(
        tool_name="get_project_stats",
        parameters={},
        version_manager=vm,
        doc_generator=doc_gen,
        config=config
    )

    assert "total_files" in result
    assert "total_size" in result
    assert "extensions" in result


def test_mcp_execute_endpoint(tmp_path):
    """Test MCP execute endpoint"""
    (tmp_path / "test.txt").write_text("Hello")

    app = create_app(tmp_path)
    client = TestClient(app)

    response = client.post("/mcp/execute", json={
        "tool": "create_snapshot",
        "parameters": {"message": "Test via MCP"}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "result" in data


def test_mcp_error_handling(tmp_path):
    """Test MCP error handling"""
    app = create_app(tmp_path)
    client = TestClient(app)

    response = client.post("/mcp/execute", json={
        "tool": "invalid_tool",
        "parameters": {}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "error" in data
