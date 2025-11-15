"""Main CLI entry point"""
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="gencodedoc",
    help="🚀 Documentation generator and intelligent versioning system",
    add_completion=False,
    no_args_is_help=True
)

console = Console()

# Import des sous-commandes
from . import snapshot_cmd, doc_cmd, config_cmd, mcp_cmd

app.add_typer(snapshot_cmd.app, name="snapshot")
app.add_typer(doc_cmd.app, name="doc")
app.add_typer(config_cmd.app, name="config")
app.add_typer(mcp_cmd.app, name="mcp")


@app.command()
def init(
    preset: Optional[str] = typer.Option(None, help="Configuration preset (python, nodejs, go, web)"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """🎬 Initialize gencodedoc in a project"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()

    console.print(f"[bold blue]Initializing gencodedoc in {project_path}[/bold blue]")

    try:
        config_manager = ConfigManager(project_path)
        config = config_manager.init_project()

        if preset:
            config_manager._apply_preset(config, preset)
            config_manager.save(config)

        # Create storage directory
        storage_path = project_path / config.storage_path
        storage_path.mkdir(exist_ok=True)

        console.print(f"[green]✅ Project initialized![/green]")
        console.print(f"   Config: {config_manager.config_path}")
        console.print(f"   Storage: {storage_path}")

        if preset:
            console.print(f"   Preset: {preset}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """📊 Show project status"""
    from ..core.config import ConfigManager
    from ..storage.database import Database

    project_path = Path(path) if path else Path.cwd()

    try:
        config_manager = ConfigManager(project_path)
        config = config_manager.load()

        db_path = project_path / config.storage_path / "gencodedoc.db"

        if not db_path.exists():
            console.print("[yellow]⚠️  No snapshots yet. Run 'gencodedoc init' first.[/yellow]")
            return

        db = Database(db_path)
        snapshots = db.list_snapshots(limit=5)

        # Summary table
        table = Table(title="Project Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project", config.project_name or project_path.name)
        table.add_row("Path", str(config.project_path))
        table.add_row("Total Snapshots", str(len(db.list_snapshots())))
        table.add_row("Autosave", "✅ Enabled" if config.autosave.enabled else "❌ Disabled")

        console.print(table)

        # Recent snapshots
        if snapshots:
            console.print("\n[bold]Recent Snapshots:[/bold]")
            snap_table = Table()
            snap_table.add_column("ID", style="cyan")
            snap_table.add_column("Date", style="magenta")
            snap_table.add_column("Message", style="green")
            snap_table.add_column("Type", style="yellow")

            for snap in snapshots[:5]:
                snap_table.add_row(
                    str(snap['id']),
                    snap['created_at'],
                    snap['message'] or "(no message)",
                    "auto" if snap['is_autosave'] else "manual"
                )

            console.print(snap_table)

    except FileNotFoundError:
        console.print("[yellow]⚠️  Project not initialized. Run 'gencodedoc init' first.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
