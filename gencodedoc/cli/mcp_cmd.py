"""MCP server commands"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional

app = typer.Typer(help="🔌 MCP server")
console = Console()


@app.command("serve")
def serve_mcp(
    host: Optional[str] = typer.Option(None, help="Host to bind to (default: 127.0.0.1)"),
    port: Optional[int] = typer.Option(None, help="Port to bind to (default: 8000)"),
    reload: bool = typer.Option(False, help="Auto-reload on code changes"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Start MCP server"""
    from ..mcp.server import create_app
    import uvicorn

    # Valeurs par défaut
    actual_host = host if host else "127.0.0.1"
    actual_port = port if port else 8000
    project_path = Path(path) if path else Path.cwd()

    console.print(f"[bold blue]Starting MCP server...[/bold blue]")
    console.print(f"   Host: {actual_host}")
    console.print(f"   Port: {actual_port}")
    console.print(f"   Project: {project_path}")

    app_instance = create_app(project_path)

    uvicorn.run(
        app_instance,
        host=actual_host,
        port=actual_port,
        reload=reload,
        log_level="info"
    )


@app.command("tools")
def list_tools():
    """List available MCP tools"""
    from ..mcp.tools import get_tools_definition
    from rich.table import Table

    tools = get_tools_definition()

    table = Table(title="Available MCP Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for tool in tools:
        table.add_row(tool["name"], tool["description"])

    console.print(table)


@app.command("config-claude")
def config_claude(
    port: Optional[int] = typer.Option(None, help="MCP server port (default: 8000)")
):
    """Generate Claude Desktop MCP configuration"""
    import json

    actual_port = port if port else 8000

    config = {
        "mcpServers": {
            "gencodedoc": {
                "url": f"http://127.0.0.1:{actual_port}/mcp",
                "description": "GenCodeDoc - Smart documentation and versioning"
            }
        }
    }

    console.print("[bold]Add this to your Claude Desktop configuration:[/bold]\n")
    console.print(json.dumps(config, indent=2))

    # Platform-specific paths
    import platform
    system = platform.system()

    console.print("\n[bold]Configuration file location:[/bold]")
    if system == "Darwin":  # macOS
        console.print("  ~/Library/Application Support/Claude/claude_desktop_config.json")
    elif system == "Windows":
        console.print("  %APPDATA%\\Claude\\claude_desktop_config.json")
    else:  # Linux
        console.print("  ~/.config/Claude/claude_desktop_config.json")
