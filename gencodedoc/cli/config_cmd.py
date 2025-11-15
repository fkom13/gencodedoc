"""Configuration management commands"""
import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
from typing import Optional

app = typer.Typer(help="⚙️ Configuration management")
console = Console()


@app.command("show")
def show_config(
    global_config: bool = typer.Option(False, "--global-config", help="Show global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show current configuration"""
    from ..core.config import ConfigManager
    import yaml

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)

    if global_config:
        config_path = config_manager.global_config_path
    else:
        config_path = config_manager.config_path

    if not config_path.exists():
        console.print(f"[yellow]No configuration file at {config_path}[/yellow]")
        return

    with open(config_path) as f:
        config_yaml = f.read()

    syntax = Syntax(config_yaml, "yaml", theme="monokai", line_numbers=True)
    console.print(f"\n[bold]Configuration: {config_path}[/bold]\n")
    console.print(syntax)


@app.command("edit")
def edit_config(
    global_config: bool = typer.Option(False, "--global-config", help="Edit global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Edit configuration file"""
    from ..core.config import ConfigManager
    import os

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)

    if global_config:
        config_path = config_manager.global_config_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        config_path = config_manager.config_path

    # Create if doesn't exist
    if not config_path.exists():
        config = config_manager.init_project()
        console.print(f"[green]Created new config at {config_path}[/green]")

    # Open in editor
    editor = os.environ.get('EDITOR', 'nano')
    os.system(f'{editor} {config_path}')

    console.print("[green]✅ Configuration updated[/green]")


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Config key (e.g., 'autosave.enabled')"),
    value: str = typer.Argument(..., help="Value to set"),
    global_config: bool = typer.Option(False, "--global-config", help="Set in global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Set a configuration value"""
    from ..core.config import ConfigManager
    import yaml

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    # Parse key path
    keys = key.split('.')

    # Navigate to nested dict
    config_dict = config.model_dump()
    target = config_dict
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    # Convert value type
    if value.lower() == 'true':
        parsed_value = True
    elif value.lower() == 'false':
        parsed_value = False
    elif value.isdigit():
        parsed_value = int(value)
    else:
        try:
            parsed_value = float(value)
        except ValueError:
            parsed_value = value

    # Set value
    target[keys[-1]] = parsed_value

    # Save
    from ..models.config import ProjectConfig
    updated_config = ProjectConfig(**config_dict)
    config_manager.save(updated_config, global_config=global_config)

    console.print(f"[green]✅ Set {key} = {parsed_value}[/green]")


@app.command("preset")
def apply_preset(
    preset: str = typer.Argument(..., help="Preset name (python, nodejs, web, go)"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Apply a configuration preset"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    config_manager._apply_preset(config, preset)
    config_manager.save(config)

    console.print(f"[green]✅ Applied preset: {preset}[/green]")


@app.command("ignore")
def manage_ignore(
    add_dir: Optional[str] = typer.Option(None, help="Add directory to ignore"),
    add_file: Optional[str] = typer.Option(None, help="Add file to ignore"),
    add_ext: Optional[str] = typer.Option(None, help="Add extension to ignore"),
    list_all: bool = typer.Option(False, help="List all ignore rules"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Manage ignore rules"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    if list_all:
        table = Table(title="Ignore Rules")
        table.add_column("Type", style="cyan")
        table.add_column("Rules", style="green")

        table.add_row("Directories", ", ".join(config.ignore.dirs))
        table.add_row("Files", ", ".join(config.ignore.files))
        table.add_row("Extensions", ", ".join(config.ignore.extensions))
        if config.ignore.patterns:
            table.add_row("Patterns", ", ".join(config.ignore.patterns))

        console.print(table)
        return

    modified = False

    if add_dir:
        if add_dir not in config.ignore.dirs:
            config.ignore.dirs.append(add_dir)
            modified = True
            console.print(f"[green]Added directory: {add_dir}[/green]")

    if add_file:
        if add_file not in config.ignore.files:
            config.ignore.files.append(add_file)
            modified = True
            console.print(f"[green]Added file: {add_file}[/green]")

    if add_ext:
        if not add_ext.startswith('.'):
            add_ext = '.' + add_ext
        if add_ext not in config.ignore.extensions:
            config.ignore.extensions.append(add_ext)
            modified = True
            console.print(f"[green]Added extension: {add_ext}[/green]")

    if modified:
        config_manager.save(config)
        console.print("[green]✅ Configuration saved[/green]")
