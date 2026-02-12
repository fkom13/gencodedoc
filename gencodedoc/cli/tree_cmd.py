"""Tree visualization command"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List
import copy

app = typer.Typer(help="🌳 Project structure visualization")
console = Console()

@app.command("tree")
def tree_command(
    path: Optional[str] = typer.Argument(None, help="Path to directory (default: current)"),
    depth: Optional[int] = typer.Option(None, "--depth", "-d", help="Maximum depth"),
    all: bool = typer.Option(False, "--all", "-a", help="Show hidden files"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(50, "--limit", "-l", help="Lines per page"),
    ignore: Optional[List[str]] = typer.Option(None, "--ignore", "-i", help="Add ignore patterns"),
    paginate: bool = typer.Option(True, help="Enable pagination (default: True)")
):
    """Show project structure tree"""
    from ..core.config import ConfigManager
    from ..utils.tree import TreeGenerator
    from ..utils.filters import FileFilter

    target_path = Path(path) if path else Path.cwd()
    
    # Load config for ignores
    try:
        config_manager = ConfigManager(target_path)
        config = config_manager.load()
        ignore_config = config.ignore
    except Exception:
        # Fallback if not a project
        from ..models.config import IgnoreConfig
        ignore_config = IgnoreConfig()
        config = None

    # Apply ad-hoc ignores
    if ignore:
        # Create a deep copy to avoid modifying global config if loaded
        ignore_config = copy.deepcopy(ignore_config)
        for pattern in ignore:
            if pattern.startswith('.'):
                ignore_config.extensions.append(pattern)
            elif '/' in pattern or '*' in pattern:
                ignore_config.patterns.append(pattern)
            else:
                ignore_config.files.append(pattern)
                ignore_config.dirs.append(pattern)

    tree_gen = TreeGenerator(show_hidden=all)
    file_filter = FileFilter(ignore_config, target_path)

    start_func = lambda p: not file_filter.should_ignore(p, p.is_dir())

    tree = tree_gen.generate(
        target_path,
        max_depth=depth,
        filter_func=start_func,
        paginate=paginate,
        page=page,
        limit=limit
    )

    console.print(f"[bold blue]📁 Project: {target_path.name}[/bold blue]")
    if paginate:
        console.print(f"[dim](Page {page}, {limit} lines/page)[/dim]")
    
    console.print(tree)
