"""Snapshot management commands"""
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from typing import Optional, List

app = typer.Typer(help="📸 Snapshot management")
console = Console()


@app.command("create")
def create_snapshot(
    message: Optional[str] = typer.Option(None, help="Snapshot message"),
    tag: Optional[str] = typer.Option(None, help="Tag for easy reference"),
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    exclude: Optional[List[str]] = typer.Option(None, help="Paths to exclude"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Create a new snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status("[bold blue]Creating snapshot..."):
        snapshot = version_manager.create_snapshot(
            message=message,
            tag=tag,
            include_paths=include,
            exclude_paths=exclude
        )

    console.print(f"[green]✅ Snapshot created![/green]")
    console.print(f"   ID: {snapshot.metadata.id}")
    console.print(f"   Files: {snapshot.metadata.files_count}")
    console.print(f"   Size: {snapshot.metadata.total_size / 1024:.1f} KB")
    if tag:
        console.print(f"   Tag: {tag}")


@app.command("list")
def list_snapshots(
    limit: int = typer.Option(10, help="Max snapshots to show"),
    all: bool = typer.Option(False, "--all", help="Include autosaves"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """List snapshots"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_date, format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    snapshots = version_manager.list_snapshots(limit=limit, include_autosave=all)

    if not snapshots:
        console.print("[yellow]No snapshots found[/yellow]")
        return

    table = Table(title=f"Snapshots ({len(snapshots)})")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="magenta")
    table.add_column("Tag", style="yellow")
    table.add_column("Message", style="green")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Type", style="blue")

    for snap in snapshots:
        table.add_row(
            str(snap.metadata.id),
            format_date(snap.metadata.created_at, "%Y-%m-%d %H:%M"),
            snap.metadata.tag or "-",
            snap.metadata.message or "-",
            str(snap.metadata.files_count),
            format_size(snap.metadata.total_size),
            "auto" if snap.metadata.is_autosave else "manual"
        )

    console.print(table)


@app.command("show")
def show_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show snapshot details"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_date, format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    snapshot = version_manager.get_snapshot(snapshot_ref)

    if not snapshot:
        console.print(f"[red]Snapshot '{snapshot_ref}' not found[/red]")
        raise typer.Exit(1)

    # Metadata table
    table = Table(title=f"Snapshot {snapshot.metadata.id}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("ID", str(snapshot.metadata.id))
    table.add_row("Date", format_date(snapshot.metadata.created_at))
    if snapshot.metadata.tag:
        table.add_row("Tag", snapshot.metadata.tag)
    if snapshot.metadata.message:
        table.add_row("Message", snapshot.metadata.message)
    table.add_row("Type", "autosave" if snapshot.metadata.is_autosave else "manual")
    table.add_row("Trigger", snapshot.metadata.trigger_type)
    table.add_row("Files", str(snapshot.metadata.files_count))
    table.add_row("Total Size", format_size(snapshot.metadata.total_size))
    table.add_row("Compressed", format_size(snapshot.metadata.compressed_size))

    console.print(table)

    # Files list
    console.print("\n[bold]Files:[/bold]")
    for file_entry in snapshot.files[:20]:  # Show first 20
        console.print(f"  • {file_entry.path}")

    if len(snapshot.files) > 20:
        console.print(f"  ... and {len(snapshot.files) - 20} more")


@app.command("restore")
def restore_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Glob patterns for partial restore"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Restore a snapshot (full or partial)"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    partial = " (partial)" if filter else ""
    if not force:
        confirm = typer.confirm(
            f"This will restore snapshot '{snapshot_ref}'{partial}. Continue?",
            default=False
        )
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    with console.status(f"[bold blue]Restoring snapshot {snapshot_ref}..."):
        result = version_manager.restore_snapshot(
            snapshot_ref, force=force, file_filters=filter
        )

    console.print(f"[green]✅ Snapshot restored{partial}![/green]")
    console.print(f"   Restored: {result['restored_count']}/{result['total_files']} files")
    if result['skipped_count'] > 0:
        console.print(f"   Skipped: {result['skipped_count']} files")


@app.command("diff")
def diff_snapshots(
    from_ref: str = typer.Argument(..., help="Source snapshot"),
    to_ref: str = typer.Argument("current", help="Target snapshot or 'current'"),
    format: str = typer.Option("unified", help="Diff format (unified/json)"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Filter diff to specific files/patterns"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Compare two snapshots, optionally filtered to specific files"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..core.differ import DiffGenerator

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status("[bold blue]Calculating diff..."):
        diff = version_manager.diff_snapshots(from_ref, to_ref, file_filters=filter)

        differ = DiffGenerator(config.diff_format, version_manager.store)
        diff_output = differ.generate_diff(diff, format=format)

    if filter:
        console.print(f"[dim]🔍 Filtered: {', '.join(filter)}[/dim]")
    console.print(diff_output)


@app.command("delete")
def delete_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Delete a snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    if not force:
        confirm = typer.confirm(
            f"Delete snapshot '{snapshot_ref}'?",
            default=False
        )
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    success = version_manager.delete_snapshot(snapshot_ref)

    if success:
        console.print("[green]✅ Snapshot deleted[/green]")
    else:
        console.print("[red]❌ Snapshot not found[/red]")
        raise typer.Exit(1)


@app.command("cat")
def cat_file_at_version(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    file_path: str = typer.Argument(..., help="Relative path of the file"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """View file content at a specific version"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from rich.syntax import Syntax
    from ..utils.formatters import get_language_from_extension

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    try:
        content = version_manager.get_file_content_at_version(snapshot_ref, file_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if content is None:
        console.print(f"[red]Could not retrieve content for '{file_path}'[/red]")
        raise typer.Exit(1)

    lang = get_language_from_extension(file_path)
    syntax = Syntax(content, lang, line_numbers=True, theme="monokai")
    console.print(f"\n[bold]📄 {file_path} @ {snapshot_ref}[/bold]\n")
    console.print(syntax)


@app.command("files")
def list_files_at_version(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    pattern: Optional[str] = typer.Option(None, help="Glob pattern to filter"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """List files in a snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    try:
        files = version_manager.list_files_at_version(snapshot_ref, pattern=pattern)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Files in snapshot {snapshot_ref} ({len(files)})")
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for f in files:
        table.add_row(f['path'], format_size(f['size']))

    console.print(table)


@app.command("export")
def export_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    output: str = typer.Argument(..., help="Output folder or archive path (.tar.gz)"),
    archive: bool = typer.Option(False, "--archive", help="Create .tar.gz archive"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Glob patterns to filter files"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Export a snapshot to a folder or archive"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status(f"[bold blue]Exporting snapshot {snapshot_ref}..."):
        result = version_manager.export_snapshot(
            snapshot_ref=snapshot_ref,
            output_path=Path(output),
            archive=archive,
            file_filters=filter
        )

    console.print(f"[green]✅ Snapshot exported![/green]")
    console.print(f"   Format: {result['format']}")
    console.print(f"   Output: {result['output_path']}")
    console.print(f"   Files: {result['exported_count']}")
    if result.get('archive_size'):
        console.print(f"   Archive size: {format_size(result['archive_size'])}")
    if result['failed_count'] > 0:
        console.print(f"   [yellow]⚠️ {result['failed_count']} files failed[/yellow]")


@app.command("cleanup")
def cleanup_orphaned(
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Remove orphaned file contents from the database"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    count = version_manager.cleanup_orphaned_contents()

    console.print(f"[green]🧹 Removed {count} orphaned content(s)[/green]")
