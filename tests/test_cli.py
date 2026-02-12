import pytest
from typer.testing import CliRunner
from gencodedoc.cli.main import app
from gencodedoc.cli.snapshot_cmd import app as snapshot_app
from gencodedoc.cli.config_cmd import app as config_app


import os

runner = CliRunner()

def test_init_command(temp_project):
    os.chdir(temp_project)
    result = runner.invoke(app, ["init", "--preset", "python"])
    assert result.exit_code == 0
    assert "Project initialized!" in result.stdout

def test_status_command(temp_project):
    os.chdir(temp_project)
    # Init and create snapshot to have status
    runner.invoke(app, ["init"])
    runner.invoke(app, ["snapshot", "create", "--message", "init"])
    
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Project Status" in result.stdout

def test_snapshot_commands(temp_project):
    os.chdir(temp_project)
    runner.invoke(app, ["init"])
    
    # Create
    result = runner.invoke(app, ["snapshot", "create", "--message", "test", "--tag", "v1"])
    assert result.exit_code == 0
    assert "Snapshot created!" in result.stdout
    
    # List
    result = runner.invoke(app, ["snapshot", "list"])
    assert result.exit_code == 0
    assert "v1" in result.stdout
    
    # Show
    result = runner.invoke(app, ["snapshot", "show", "v1"])
    assert result.exit_code == 0
    assert "Snapshot Details" not in result.stdout # Title is "Snapshot {id}" or similar
    assert "v1" in result.stdout

def test_config_commands(temp_project):
    os.chdir(temp_project)
    runner.invoke(app, ["init"])
    
    # Show
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    
    # Set
    result = runner.invoke(app, ["config", "set", "autosave.enabled", "true"])
    assert result.exit_code == 0
    assert "Set autosave.enabled = True" in result.stdout
    
    # Check
    result = runner.invoke(app, ["config", "show"])
    assert "enabled" in result.stdout
    assert "True" in result.stdout or "true" in result.stdout

def test_doc_generate_command(temp_project):
    os.chdir(temp_project)
    runner.invoke(app, ["init"])
    
    result = runner.invoke(app, ["doc", "generate"])
    assert result.exit_code == 0
    assert "Documentation generated" in result.stdout

