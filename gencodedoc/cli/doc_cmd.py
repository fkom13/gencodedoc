"""Documentation generation commands"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List

app = typer.Typer(help="📚 Documentation generation")
console = Console()


@app.command("generate")
def generate_doc(
    output: Optional[Path] = typer.Option(None, help="Output file path"),
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    exclude: Optional[List[str]] = typer.Option(None, help="Paths to exclude"),
    tree: bool = typer.Option(True, "--tree/--no-tree", help="Include directory tree"),
    code: bool = typer.Option(True, "--code/--no-code", help="Include file code"),
    tree_full: bool = typer.Option(False, "--tree-full/--no-tree-full", help="Full tree, selected code only"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Generate project documentation"""
    from ..core.config import ConfigManager
    from ..core.documentation import DocumentationGenerator

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    doc_gen = DocumentationGenerator(config)

    with console.status("[bold blue]Generating documentation..."):
        output_path = doc_gen.generate(
            output_path=output,
            include_paths=include,
            exclude_paths=exclude,
            include_tree=tree,
            include_code=code,
            tree_full_code_select=tree_full
        )

    file_size = output_path.stat().st_size / 1024
    console.print(f"[green]✅ Documentation generated![/green]")
    console.print(f"   Output: {output_path}")
    console.print(f"   Size: {file_size:.1f} KB")


@app.command("preview")
def preview_structure(
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    max_depth: Optional[int] = typer.Option(None, help="Max tree depth"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Preview project structure"""
    from ..core.config import ConfigManager
    from ..utils.tree import TreeGenerator
    from ..utils.filters import FileFilter

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    tree_gen = TreeGenerator()
    file_filter = FileFilter(config.ignore, config.project_path)

    console.print(f"[bold blue]Project Structure: {config.project_name}[/bold blue]\n")

    tree = tree_gen.generate(
        config.project_path,
        max_depth=max_depth,
        filter_func=lambda p: not file_filter.should_ignore(p, p.is_dir())
    )

    console.print(tree)


@app.command("stats")
def show_stats(
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show project statistics"""
    from ..core.config import ConfigManager
    from ..core.scanner import FileScanner
    from ..utils.formatters import format_size
    from rich.table import Table
    from collections import Counter

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    scanner = FileScanner(config)

    with console.status("[bold blue]Scanning project..."):
        files = scanner.scan(include_paths=include)

    # Calculate stats
    total_size = sum(f.size for f in files)
    extensions = Counter(Path(f.path).suffix for f in files)

    # Summary table
    summary = Table(title="Project Statistics")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green", justify="right")

    summary.add_row("Total Files", str(len(files)))
    summary.add_row("Total Size", format_size(total_size))
    summary.add_row("Unique Extensions", str(len(extensions)))

    console.print(summary)

    # Extensions table
    if extensions:
        ext_table = Table(title="Files by Extension")
        ext_table.add_column("Extension", style="cyan")
        ext_table.add_column("Count", style="green", justify="right")
        ext_table.add_column("Percentage", style="yellow", justify="right")

        for ext, count in extensions.most_common(10):
            ext_name = ext if ext else "(no extension)"
            percentage = (count / len(files)) * 100
            ext_table.add_row(ext_name, str(count), f"{percentage:.1f}%")

        console.print("\n")
        console.print(ext_table)
