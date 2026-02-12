# gencodedoc (Partie 2)
> Suite de la documentation (12/02/2026)

### 📄 `gencodedoc/core/__init__.py`

```python
"""Core functionality"""
from .config import ConfigManager
from .scanner import FileScanner
from .versioning import VersionManager
from .documentation import DocumentationGenerator
from .differ import DiffGenerator
from .autosave import AutosaveManager

__all__ = [
    "ConfigManager",
    "FileScanner",
    "VersionManager",
    "DocumentationGenerator",
    "DiffGenerator",
    "AutosaveManager",
]

```

### 📄 `gencodedoc/core/autosave.py`

```python
"""Intelligent autosave system"""
import time
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..models.config import ProjectConfig
from .versioning import VersionManager


class AutosaveHandler(FileSystemEventHandler):
    """File system event handler for autosave"""

    def __init__(self, manager: 'AutosaveManager'):
        self.manager = manager
        self.last_event = datetime.now()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Debounce events (ignore if too frequent)
        now = datetime.now()
        if (now - self.last_event).total_seconds() < 1:
            return

        self.last_event = now
        self.manager.on_file_change()


class AutosaveManager:
    """Manages intelligent autosave"""

    def __init__(self, config: ProjectConfig, version_manager: VersionManager):
        self.config = config
        self.version_manager = version_manager

        self.observer: Optional[Observer] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.running = False

        self.last_save = datetime.now()
        self.changes_detected = False

    def start(self) -> None:
        """Start autosave"""
        if not self.config.autosave.enabled:
            return

        self.running = True
        mode = self.config.autosave.mode

        if mode == 'timer':
            self._start_timer_mode()
        elif mode == 'diff':
            self._start_diff_mode()
        elif mode == 'hybrid':
            self._start_hybrid_mode()

    def stop(self) -> None:
        """Stop autosave"""
        self.running = False

        if self.observer:
            self.observer.stop()
            self.observer.join()

        if self.timer_thread:
            self.timer_thread.join()

    def _start_timer_mode(self) -> None:
        """Start timer-based autosave"""
        interval = self.config.autosave.timer.interval

        def timer_loop():
            while self.running:
                time.sleep(interval)
                if self.running:
                    self._create_autosave('timer')

        self.timer_thread = threading.Thread(target=timer_loop, daemon=True)
        self.timer_thread.start()

    def _start_diff_mode(self) -> None:
        """Start diff-based autosave"""
        # Watch file system
        self.observer = Observer()
        handler = AutosaveHandler(self)
        self.observer.schedule(
            handler,
            str(self.config.project_path),
            recursive=True
        )
        self.observer.start()

        # Periodic check thread
        check_interval = self.config.autosave.diff_threshold.check_interval

        def check_loop():
            while self.running:
                time.sleep(check_interval)
                if self.running and self.changes_detected:
                    if self._should_save_diff():
                        self._create_autosave('diff_threshold')
                        self.changes_detected = False

        self.timer_thread = threading.Thread(target=check_loop, daemon=True)
        self.timer_thread.start()

    def _start_hybrid_mode(self) -> None:
        """Start hybrid autosave (timer OR diff)"""
        # Watch file system
        self.observer = Observer()
        handler = AutosaveHandler(self)
        self.observer.schedule(
            handler,
            str(self.config.project_path),
            recursive=True
        )
        self.observer.start()

        def hybrid_loop():
            while self.running:
                time.sleep(60)  # Check every minute

                if not self.running:
                    break

                now = datetime.now()
                time_since_save = (now - self.last_save).total_seconds()

                # Check max interval
                if time_since_save >= self.config.autosave.hybrid.max_interval:
                    self._create_autosave('hybrid_max_interval')

                # Check min interval + changes
                elif (time_since_save >= self.config.autosave.hybrid.min_interval and
                      self.changes_detected and
                      self._should_save_diff()):
                    self._create_autosave('hybrid_threshold')
                    self.changes_detected = False

        self.timer_thread = threading.Thread(target=hybrid_loop, daemon=True)
        self.timer_thread.start()

    def on_file_change(self) -> None:
        """Called when file changes detected"""
        self.changes_detected = True

    def _should_save_diff(self) -> bool:
        """Check if changes are significant enough to save"""
        try:
            # Get latest snapshot
            latest = self.version_manager.store.db.get_latest_snapshot()
            if not latest:
                return True  # No previous snapshot, save

            # Compare with current state
            diff = self.version_manager.diff_snapshots(
                str(latest['id']),
                'current'
            )

            # Check threshold
            threshold = (
                self.config.autosave.diff_threshold.threshold
                if self.config.autosave.mode == 'diff'
                else self.config.autosave.hybrid.threshold
            )

            return diff.significance_score >= threshold

        except Exception:
            return False

    def _create_autosave(self, trigger_type: str) -> None:
        """Create an autosave snapshot"""
        try:
            self.version_manager.create_snapshot(
                message=f"Autosave ({trigger_type})",
                is_autosave=True,
                trigger_type=trigger_type
            )
            self.last_save = datetime.now()

            # Cleanup old autosaves
            max_keep = self.config.autosave.retention.max_autosaves
            self.version_manager.cleanup_old_autosaves(max_keep)
            
            # Cleanup expired autosaves
            delete_after_days = self.config.autosave.retention.delete_after_days
            if delete_after_days > 0:
                self.version_manager.cleanup_expired_autosaves(delete_after_days)

        except Exception as e:
            print(f"Autosave failed: {e}")

```

### 📄 `gencodedoc/core/config.py`

```python
"""Configuration management"""
import yaml
from pathlib import Path
from typing import Optional
from ..models.config import ProjectConfig

class ConfigManager:
    """Manages project and global configuration"""

    DEFAULT_CONFIG_NAME = ".gencodedoc.yaml"
    GLOBAL_CONFIG_DIR = Path.home() / ".config" / "gencodedoc"

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.config_path = self.project_path / self.DEFAULT_CONFIG_NAME
        self.global_config_path = self.GLOBAL_CONFIG_DIR / "config.yaml"
        self._config: Optional[ProjectConfig] = None

    def load(self) -> ProjectConfig:
        """Load configuration: global -> project"""
        config_dict = {}

        # Global config
        if self.global_config_path.exists():
            with open(self.global_config_path) as f:
                global_config = yaml.safe_load(f) or {}
                config_dict.update(global_config)

        # Project config (overrides global)
        if self.config_path.exists():
            with open(self.config_path) as f:
                project_config = yaml.safe_load(f) or {}
                config_dict = self._deep_merge(config_dict, project_config)

        # Convert paths
        if 'storage_path' in config_dict:
            config_dict['storage_path'] = Path(config_dict['storage_path'])

        # ✅ CORRECTION : Toujours injecter le project_path
        config_dict['project_path'] = self.project_path

        self._config = ProjectConfig(**config_dict)
        # La ligne ci-dessous devient redondante mais non nuisible
        self._config.project_path = self.project_path

        return self._config

    def save(self, config: ProjectConfig, global_config: bool = False) -> None:
        """Save configuration to file"""
        target_path = self.global_config_path if global_config else self.config_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Deduplicate ignore lists (preserves order)
        if config.ignore:
            config.ignore.dirs = list(dict.fromkeys(config.ignore.dirs))
            config.ignore.files = list(dict.fromkeys(config.ignore.files))
            config.ignore.extensions = list(dict.fromkeys(config.ignore.extensions))
            config.ignore.patterns = list(dict.fromkeys(config.ignore.patterns))

        config_dict = config.model_dump(
            exclude={'project_path'},
            exclude_none=True,
            mode='json'
        )

        # Convert Path to string
        if 'storage_path' in config_dict:
            config_dict['storage_path'] = str(config_dict['storage_path'])

        with open(target_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    def init_project(self, preset: Optional[str] = None) -> ProjectConfig:
        """Initialize new project with config"""
        config = ProjectConfig(
            project_name=self.project_path.name,
            project_path=self.project_path
        )

        # Auto-detect ignore patterns
        config.ignore = self._detect_ignore_patterns()

        # Apply preset
        if preset:
            self._apply_preset(config, preset)

        self.save(config)
        return config

    def _detect_ignore_patterns(self):
        """Auto-detect ignore patterns"""
        from ..models.config import IgnoreConfig

        ignore = IgnoreConfig()

        # Python
        if (self.project_path / "requirements.txt").exists() or \
           (self.project_path / "pyproject.toml").exists():
            ignore.dirs.extend(['venv', '.venv', '__pycache__'])
            ignore.extensions.extend(['.pyc', '.pyo'])

        # Node.js
        if (self.project_path / "package.json").exists():
            ignore.dirs.extend(['node_modules', 'dist', '.next'])

        # Go
        if (self.project_path / "go.mod").exists():
            ignore.dirs.append('vendor')

        return ignore

    def _apply_preset(self, config: ProjectConfig, preset: str) -> None:
        """Apply preset from YAML or fallback to built-in"""
        # Try loading from YAML file in generic config dir
        preset_path = Path(__file__).parent.parent / "config" / "presets" / f"{preset}.yaml"
        
        if preset_path.exists():
            try:
                with open(preset_path) as f:
                    p = yaml.safe_load(f) or {}
                    if 'ignore' in p:
                        p = p['ignore']  # Handle nested 'ignore' key if present or flat structure
            except Exception:
                p = {} # Fallback on error
        else:
            # Fallback to hardcoded presets
            presets = {
                'python': {
                    'dirs': ['venv', '.venv', '__pycache__', 'dist', 'build', '.git', '.idea', '.vscode'],
                    'extensions': ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.class'],
                    'files': ['.DS_Store', 'Thumbs.db']
                },
                'nodejs': {
                    'dirs': ['node_modules', 'dist', 'build', 'coverage', '.git'],
                    'files': ['package-lock.json', 'yarn.lock', '.DS_Store']
                },
                'web': {
                    'dirs': ['node_modules', 'dist', '.git'],
                    'extensions': ['.map', '.min.js', '.css.map']
                },
                'go': {
                    'dirs': ['vendor', 'bin', '.git'],
                    'extensions': ['.exe', '.test']
                }
            }
            p = presets.get(preset, {})

        if 'dirs' in p:
            config.ignore.dirs.extend([d for d in p['dirs'] if d not in config.ignore.dirs])
        if 'files' in p:
            config.ignore.files.extend([f for f in p['files'] if f not in config.ignore.files])
        if 'extensions' in p:
            config.ignore.extensions.extend([e for e in p['extensions'] if e not in config.ignore.extensions])

    @staticmethod
    def _deep_merge(dict1: dict, dict2: dict) -> dict:
        """Deep merge dicts"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @property
    def config(self) -> ProjectConfig:
        """Get config (lazy load)"""
        if self._config is None:
            self._config = self.load()
        return self._config

```

### 📄 `gencodedoc/core/differ.py`

```python
"""Diff generation in multiple formats"""
import difflib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from ..models.snapshot import SnapshotDiff, DiffEntry
from ..models.config import DiffFormatConfig
from ..storage.snapshot_store import SnapshotStore


class DiffGenerator:
    """Generate diffs in various formats"""

    def __init__(self, config: DiffFormatConfig, store: SnapshotStore):
        self.config = config
        self.store = store

    def generate_diff(
        self,
        snapshot_diff: SnapshotDiff,
        format: Optional[str] = None
    ) -> str:
        """
        Generate diff in specified format

        Args:
            snapshot_diff: Diff between snapshots
            format: Output format (unified, json, ast)

        Returns:
            Formatted diff string
        """
        format = format or self.config.default

        if format == 'unified':
            return self._generate_unified(snapshot_diff)
        elif format == 'json':
            return self._generate_json(snapshot_diff)
        elif format == 'markdown':
            return self._generate_markdown(snapshot_diff)
        elif format == 'ast':
            return self._generate_ast(snapshot_diff)
        else:
            raise ValueError(f"Unknown diff format: {format}")

    def _generate_unified(self, diff: SnapshotDiff) -> str:
        """Generate unified diff format (like git diff)"""
        lines = []

        # Header
        lines.append(f"Diff from snapshot {diff.from_snapshot} to {diff.to_snapshot}")
        lines.append(f"Total changes: {diff.total_changes}")
        lines.append(f"Significance: {diff.significance_score:.2%}\n")

        # Added files
        if diff.files_added:
            lines.append(f"=== Added files ({len(diff.files_added)}) ===")
            for path in diff.files_added:
                lines.append(f"+ {path}")
            lines.append("")

        # Removed files
        if diff.files_removed:
            lines.append(f"=== Removed files ({len(diff.files_removed)}) ===")
            for path in diff.files_removed:
                lines.append(f"- {path}")
            lines.append("")

        # Modified files
        if diff.files_modified:
            lines.append(f"=== Modified files ({len(diff.files_modified)}) ===")
            for entry in diff.files_modified:
                lines.append(f"\n--- {entry.file_path}")

                # Get file contents
                old_content = self._get_file_content(entry.old_hash)
                new_content = self._get_file_content(entry.new_hash)

                if old_content and new_content:
                    # Generate unified diff
                    unified = difflib.unified_diff(
                        old_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=f"a/{entry.file_path}",
                        tofile=f"b/{entry.file_path}",
                        lineterm='',
                        n=self.config.unified_context
                    )
                    lines.extend(unified)
                else:
                    lines.append("(Binary file or content not available)")

        return '\n'.join(lines)

    def _generate_json(self, diff: SnapshotDiff) -> str:
        """Generate JSON diff format"""
        result = {
            "from_snapshot": diff.from_snapshot,
            "to_snapshot": diff.to_snapshot,
            "total_changes": diff.total_changes,
            "significance_score": diff.significance_score,
            "changes": {
                "added": diff.files_added,
                "removed": diff.files_removed,
                "modified": []
            }
        }

        # Add modified files details
        for entry in diff.files_modified:
            mod_entry = {
                "file_path": entry.file_path,
                "status": entry.status,
                "old_hash": entry.old_hash,
                "new_hash": entry.new_hash
            }

            if self.config.json_include_content:
                old_content = self._get_file_content(entry.old_hash)
                new_content = self._get_file_content(entry.new_hash)

                if old_content and new_content:
                    mod_entry["old_content"] = old_content
                    mod_entry["new_content"] = new_content

            result["changes"]["modified"].append(mod_entry)

        return json.dumps(result, indent=2)

    def _generate_markdown(self, diff: SnapshotDiff) -> str:
        """Generate Markdown-formatted diff (LLM & human-friendly)"""
        lines = []

        lines.append(f"## 📊 Diff: `{diff.from_snapshot}` → `{diff.to_snapshot}`")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total changes | **{diff.total_changes}** |")
        lines.append(f"| Significance | **{diff.significance_score:.1%}** |")
        lines.append(f"| Files added | {len(diff.files_added)} |")
        lines.append(f"| Files removed | {len(diff.files_removed)} |")
        lines.append(f"| Files modified | {len(diff.files_modified)} |")
        lines.append("")

        if diff.files_added:
            lines.append("### ➕ Added Files")
            for path in diff.files_added:
                lines.append(f"- `{path}`")
            lines.append("")

        if diff.files_removed:
            lines.append("### ➖ Removed Files")
            for path in diff.files_removed:
                lines.append(f"- ~~`{path}`~~")
            lines.append("")

        if diff.files_modified:
            lines.append("### ✏️ Modified Files")
            for entry in diff.files_modified:
                lines.append(f"\n#### `{entry.file_path}`")

                old_content = self._get_file_content(entry.old_hash)
                new_content = self._get_file_content(entry.new_hash)

                if old_content and new_content:
                    unified = list(difflib.unified_diff(
                        old_content.splitlines(keepends=True),
                        new_content.splitlines(keepends=True),
                        fromfile=f"a/{entry.file_path}",
                        tofile=f"b/{entry.file_path}",
                        lineterm='',
                        n=self.config.unified_context
                    ))
                    if unified:
                        lines.append("```diff")
                        lines.extend(unified)
                        lines.append("```")
                    else:
                        lines.append("*(No visible content changes)*")
                else:
                    lines.append("*(Binary or unavailable)*")

        return '\n'.join(lines)

    def _generate_ast(self, diff: SnapshotDiff) -> str:
        """
        Generate AST-based semantic diff

        Note: This is a placeholder. Full AST diff would require
        language-specific parsers (tree-sitter, etc.)
        """
        lines = [
            "=== AST-based Semantic Diff ===",
            "(AST diff requires language-specific parsers)",
            "",
            "Summary:",
            f"  Files added: {len(diff.files_added)}",
            f"  Files removed: {len(diff.files_removed)}",
            f"  Files modified: {len(diff.files_modified)}",
            ""
        ]

        # For now, fall back to unified diff
        lines.append("Falling back to unified diff:")
        lines.append("")
        lines.append(self._generate_unified(diff))

        return '\n'.join(lines)

    def _get_file_content(self, file_hash: Optional[str]) -> Optional[str]:
        """Get file content from storage"""
        if not file_hash:
            return None

        try:
            compressed = self.store.db.get_content(file_hash)
            if not compressed:
                return None

            decompressed = self.store.compressor.decompress(compressed)
            return decompressed.decode('utf-8', errors='replace')
        except Exception:
            return None

```

### 📄 `gencodedoc/core/documentation.py`

```python
"""Documentation generation (port from JS)"""
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
from ..models.config import ProjectConfig
from ..utils.tree import TreeGenerator
from ..utils.formatters import get_language_from_extension
from ..utils.filters import FileFilter

class SmartSplitter:
    """Handles splitting documentation into multiple parts based on line limit"""
    def __init__(self, base_path: Path, limit: Optional[int], project_name: str):
        self.base_path = base_path
        self.limit = limit
        self.project_name = project_name
        self.parts: List[str] = []
        self.current_content: List[str] = []
        self.current_lines = 0
        self.part_number = 1
        self.header = ""

    def set_header(self, header: str):
        self.header = header
        self.current_content.append(header)
        self.current_lines += header.count('\n') + 1

    def add(self, content: str):
        if not self.limit:
            self.current_content.append(content)
            return

        lines = content.count('\n') + 1
        
        # If adding this content exceeds limit (and we have substantial content already)
        if self.current_lines + lines > self.limit and self.current_lines > 100:
            self._finalize_part()
            self._start_new_part()
        
        self.current_content.append(content)
        self.current_lines += lines

    def _finalize_part(self):
        content = "".join(self.current_content)
        if self.parts: # Not the first part
             content += "\n\n---\n**🚀 Suite dans la partie suivante...**"
        self.parts.append(content)

    def _start_new_part(self):
        self.part_number += 1
        self.current_content = []
        self.current_lines = 0
        
        # Add context header
        context_header = f"# {self.project_name} (Partie {self.part_number})\n> Suite de la documentation ({datetime.now().strftime('%d/%m/%Y')})\n\n"
        self.current_content.append(context_header)
        self.current_lines += context_header.count('\n') + 1

    def save(self) -> List[Path]:
        if self.current_content:
            self.parts.append("".join(self.current_content))
            
        generated_files = []
        
        if len(self.parts) == 1:
            self.base_path.write_text(self.parts[0], encoding='utf-8')
            generated_files.append(self.base_path)
        else:
            # Multi-part naming: output.md -> output_part1.md, output_part2.md
            stem = self.base_path.stem
            suffix = self.base_path.suffix
            parent = self.base_path.parent
            
            for i, content in enumerate(self.parts, 1):
                part_path = parent / f"{stem}_part{i}{suffix}"
                
                # Add footer for last part
                if i == len(self.parts):
                    content += "\n\n---\n**✅ Fin de la documentation.**"
                elif i < len(self.parts):
                     # Ensure continuity marker is present (added in _finalize_part for others)
                     pass

                part_path.write_text(content, encoding='utf-8')
                generated_files.append(part_path)
                
        return generated_files

class DocumentationGenerator:
    """Generate markdown documentation"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.tree_gen = TreeGenerator()
        self.filter = FileFilter(config.ignore, config.project_path)

    def generate(
        self,
        output_path: Optional[Path] = None,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_tree: Optional[bool] = None,
        include_code: Optional[bool] = None,
        tree_full_code_select: Optional[bool] = None,
        split_limit: Optional[int] = None,
        ignore_tree_patterns: Optional[List[str]] = None
    ) -> List[Path]: # Returns list of generated files
        """Generate documentation"""
        # Use config defaults
        if include_tree is None:
            include_tree = self.config.output.include_tree
        if include_code is None:
            include_code = self.config.output.include_code
        if tree_full_code_select is None:
            tree_full_code_select = self.config.output.tree_full_code_select

        # Generate output filename
        if output_path is None:
            output_path = self._generate_output_path(split_limit is not None)

        # Collect files
        files = self._collect_files(include_paths, exclude_paths)
        
        # Initialize splitter
        project_name = self.config.project_name or self.config.project_path.name
        splitter = SmartSplitter(output_path, split_limit, project_name)

        # Header
        header = f"# Documentation du projet: {project_name}\n"
        header += f"> Généré le {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        splitter.set_header(header)

        # Tree
        if include_tree:
            splitter.add("## 📂 Structure du projet\n\n")
            splitter.add("```\n")

            # Combine default ignore + specific tree ignore
            def tree_filter(p: Path) -> bool:
                # 1. Check standard ignore rules
                if self.filter.should_ignore(p, p.is_dir()):
                    return False
                
                # 2. Check specific tree ignore patterns
                if ignore_tree_patterns:
                    from fnmatch import fnmatch
                    name = p.name
                    for pattern in ignore_tree_patterns:
                        if fnmatch(name, pattern):
                            return False
                return True

            if tree_full_code_select and files:
                # Full tree but mark selected
                selected_set = set(files)
                tree = self.tree_gen.generate_with_selection(
                    self.config.project_path,
                    selected_set,
                    tree_filter
                )
            else:
                # Normal tree
                tree = self.tree_gen.generate(
                    self.config.project_path,
                    filter_func=tree_filter
                )

            splitter.add(tree)
            splitter.add("```\n\n")

        # File contents
        if include_code:
            splitter.add("## 📝 Contenu des fichiers\n\n")

            for file_path in files:
                relative_path = file_path.relative_to(self.config.project_path)
                
                # Prepare file block
                block = f"### 📄 `{relative_path}`\n\n"
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if self.config.output.language_detection:
                        lang = get_language_from_extension(str(file_path))
                    else:
                        lang = 'text'
                    block += f"```{lang}\n{content}\n```\n\n"
                except Exception as e:
                    block += f"```\nErreur lors de la lecture: {e}\n```\n\n"
                
                splitter.add(block)

        # Save all parts
        return splitter.save()

    def _generate_output_path(self, is_split: bool = False) -> Path:
        """Generate output filename"""
        template = self.config.output.default_name
        
        filename = template.format(
            project=self.config.project_name or self.config.project_path.name,
            date=datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        
        return self.config.project_path / filename

    def _collect_files(
        self,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ) -> List[Path]:
        """Collect files to document"""
        if include_paths:
            files = []
            for path_str in include_paths:
                path = self.config.project_path / path_str
                if path.exists():
                    if path.is_file():
                        files.append(path)
                    elif path.is_dir():
                        files.extend(list(self.filter.scan_directory(path)))
        else:
            files = list(self.filter.scan_directory(self.config.project_path))

        # Apply exclusions
        if exclude_paths:
            import fnmatch
            
            final_files = []
            for f in files:
                should_exclude = False
                relative_path = f.relative_to(self.config.project_path)
                
                for ex_path in exclude_paths:
                     # Check if file matches exclusion pattern or path
                     # Force forward slashes for consistency with config patterns
                     rel_str = str(relative_path).replace('\\', '/')
                     if fnmatch.fnmatch(f.name, ex_path) or fnmatch.fnmatch(rel_str, ex_path):
                         should_exclude = True
                         break
                
                if not should_exclude:
                    final_files.append(f)
            files = final_files

        # Filter by max size
        max_size = self.config.output.max_file_size
        files = [f for f in files if f.stat().st_size <= max_size]

        return sorted(files)

```

### 📄 `gencodedoc/core/scanner.py`

```python
"""File scanning functionality"""
import hashlib
from pathlib import Path
from typing import List, Optional
from ..models.snapshot import FileEntry
from ..models.config import ProjectConfig
from ..utils.filters import FileFilter, BinaryDetector

class FileScanner:
    """Scans project files with filtering"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.filter = FileFilter(config.ignore, config.project_path)
        self.binary_detector = BinaryDetector()

    def scan(
        self,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_binary: bool = False
    ) -> List[FileEntry]:
        """Scan project files"""
        if include_paths:
            files = self._scan_specific_paths(include_paths)
        else:
            files = list(self.filter.scan_directory(self.config.project_path))

        if exclude_paths:
            exclude_set = {self.config.project_path / p for p in exclude_paths}
            files = [f for f in files if f not in exclude_set]

        if not include_binary:
            files = [f for f in files if not self.binary_detector.is_binary(f)]

        return self._create_file_entries(files)

    def _scan_specific_paths(self, paths: List[str]) -> List[Path]:
        """Scan specific paths"""
        files = []

        for path_str in paths:
            path = self.config.project_path / path_str

            if not path.exists():
                continue

            if path.is_file():
                if not self.filter.should_ignore(path, False):
                    files.append(path)
            elif path.is_dir():
                files.extend(list(self.filter.scan_directory(path)))

        return files

    def _create_file_entries(self, files: List[Path]) -> List[FileEntry]:
        """Convert Path to FileEntry"""
        entries = []

        for file_path in files:
            try:
                file_hash = self._calculate_file_hash(file_path)
                stat = file_path.stat()

                try:
                    relative_path = file_path.relative_to(self.config.project_path)
                except ValueError:
                    relative_path = file_path

                entry = FileEntry(
                    path=str(relative_path),
                    hash=file_hash,
                    size=stat.st_size,
                    mode=stat.st_mode
                )
                entries.append(entry)

            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}")
                continue

        return entries

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA256 hash"""
        hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

```

### 📄 `gencodedoc/core/versioning.py`

```python
"""Version management and snapshot operations"""
import tarfile
import io
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.config import ProjectConfig
from ..models.snapshot import Snapshot, SnapshotDiff, DiffEntry
from ..storage.snapshot_store import SnapshotStore
from .scanner import FileScanner

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages snapshots and versioning"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.scanner = FileScanner(config)

        # Initialize storage
        storage_path = config.project_path / config.storage_path
        self.store = SnapshotStore(
            storage_path=storage_path,
            project_path=config.project_path,
            compression_level=config.compression_level,
            compression_enabled=config.compression_enabled
        )

    def create_snapshot(
        self,
        message: Optional[str] = None,
        tag: Optional[str] = None,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        is_autosave: bool = False,
        trigger_type: str = 'manual'
    ) -> Snapshot:
        """
        Create a new snapshot

        Args:
            message: Optional commit message
            tag: Optional tag for easy reference (e.g., 'before-refactor')
            include_paths: Specific paths to include
            exclude_paths: Specific paths to exclude
            is_autosave: Whether this is an autosave
            trigger_type: What triggered the snapshot

        Returns:
            Created snapshot
        """
        # Scan files
        files = self.scanner.scan(
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            include_binary=False
        )

        # Create snapshot
        snapshot = self.store.create_snapshot(
            files=files,
            message=message,
            tag=tag,
            is_autosave=is_autosave,
            trigger_type=trigger_type
        )

        return snapshot

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        include_autosave: bool = True
    ) -> List[Snapshot]:
        """List all snapshots"""
        metadata_list = self.store.list_snapshots(limit, include_autosave)

        # Convert to full snapshots
        snapshots = []
        for metadata in metadata_list:
            if metadata.id:
                snapshot = self.store.get_snapshot(metadata.id)
                if snapshot:
                    snapshots.append(snapshot)

        return snapshots

    def get_snapshot(self, snapshot_ref: str) -> Optional[Snapshot]:
        """
        Get snapshot by ID or tag

        Args:
            snapshot_ref: Snapshot ID (number) or tag (string)

        Returns:
            Snapshot or None
        """
        # Try as ID first
        try:
            snapshot_id = int(snapshot_ref)
            return self.store.get_snapshot(snapshot_id)
        except ValueError:
            # Try as tag
            return self.store.get_snapshot_by_tag(snapshot_ref)

    # ────────────────────────────────────────────
    # File content viewing
    # ────────────────────────────────────────────

    def get_file_content_at_version(
        self,
        snapshot_ref: str,
        file_path: str
    ) -> Optional[str]:
        """
        Get the content of a specific file at a specific snapshot version

        Args:
            snapshot_ref: Snapshot ID or tag
            file_path: Relative path of the file

        Returns:
            File content as string, or None if not found
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        file_entry = snapshot.get_file(file_path)
        if not file_entry:
            raise ValueError(f"File '{file_path}' not found in snapshot '{snapshot_ref}'")

        content = self.store.get_file_content(file_entry.hash)
        if content is None:
            logger.warning(f"Content for hash {file_entry.hash} not found in store")
        return content

    def list_files_at_version(
        self,
        snapshot_ref: str,
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all files present in a specific snapshot version

        Args:
            snapshot_ref: Snapshot ID or tag
            pattern: Optional glob pattern to filter files

        Returns:
            List of file info dicts with path, size, hash
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        if pattern:
            files = snapshot.get_files_matching([pattern])
        else:
            files = snapshot.files

        return [
            {
                'path': f.path,
                'size': f.size,
                'hash': f.hash,
                'mode': f.mode
            }
            for f in sorted(files, key=lambda x: x.path)
        ]

    # ────────────────────────────────────────────
    # Restore operations
    # ────────────────────────────────────────────

    def restore_snapshot(
        self,
        snapshot_ref: str,
        target_dir: Optional[Path] = None,
        force: bool = False,
        file_filters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore a snapshot (full or partial)

        Args:
            snapshot_ref: Snapshot ID or tag
            target_dir: Where to restore (default: project root)
            force: Overwrite existing files
            file_filters: Optional list of glob patterns/paths to restore selectively

        Returns:
            Dict with restore details: restored_count, skipped_count, files_restored
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        if target_dir is None:
            target_dir = self.config.project_path

        # Determine which files to restore
        if file_filters:
            files_to_restore = snapshot.get_files_matching(file_filters)
        else:
            files_to_restore = snapshot.files

        restored = []
        skipped = []

        for file_entry in files_to_restore:
            target_path = target_dir / file_entry.path

            # Check if file exists
            if target_path.exists() and not force:
                skipped.append(file_entry.path)
                continue

            # Restore file
            if self.store.restore_file(file_entry.hash, target_path):
                target_path.chmod(file_entry.mode)
                restored.append(file_entry.path)
            else:
                logger.warning(f"Failed to restore {file_entry.path}")
                skipped.append(file_entry.path)

        return {
            'restored_count': len(restored),
            'skipped_count': len(skipped),
            'total_files': len(files_to_restore),
            'files_restored': restored,
            'files_skipped': skipped
        }

    # ────────────────────────────────────────────
    # Export operations
    # ────────────────────────────────────────────

    def export_snapshot(
        self,
        snapshot_ref: str,
        output_path: Path,
        archive: bool = False,
        file_filters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Export a snapshot to a folder or tar.gz archive

        Args:
            snapshot_ref: Snapshot ID or tag
            output_path: Target folder or archive path (.tar.gz)
            archive: If True, create a .tar.gz archive
            file_filters: Optional glob/path filters

        Returns:
            Dict with export details
        """
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            raise ValueError(f"Snapshot '{snapshot_ref}' not found")

        # Determine which files to export
        if file_filters:
            files_to_export = snapshot.get_files_matching(file_filters)
        else:
            files_to_export = snapshot.files

        if archive:
            return self._export_as_archive(snapshot, files_to_export, output_path)
        else:
            return self._export_as_folder(snapshot, files_to_export, output_path)

    def _export_as_folder(
        self,
        snapshot: Snapshot,
        files: list,
        output_path: Path
    ) -> Dict[str, Any]:
        """Export snapshot files to a folder"""
        output_path.mkdir(parents=True, exist_ok=True)
        exported = []
        failed = []

        for file_entry in files:
            target = output_path / file_entry.path
            content_bytes = self.store.get_file_content_bytes(file_entry.hash)

            if content_bytes is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content_bytes)
                target.chmod(file_entry.mode)
                exported.append(file_entry.path)
            else:
                failed.append(file_entry.path)

        tag = snapshot.metadata.tag or str(snapshot.metadata.id)
        return {
            'snapshot': tag,
            'format': 'folder',
            'output_path': str(output_path),
            'exported_count': len(exported),
            'failed_count': len(failed),
            'files_exported': exported,
            'files_failed': failed
        }

    def _export_as_archive(
        self,
        snapshot: Snapshot,
        files: list,
        output_path: Path
    ) -> Dict[str, Any]:
        """Export snapshot as tar.gz archive"""
        output_path = Path(str(output_path))
        if not str(output_path).endswith('.tar.gz'):
            output_path = output_path.with_suffix('.tar.gz')

        output_path.parent.mkdir(parents=True, exist_ok=True)
        exported = []
        failed = []

        with tarfile.open(str(output_path), 'w:gz') as tar:
            for file_entry in files:
                content_bytes = self.store.get_file_content_bytes(file_entry.hash)

                if content_bytes is not None:
                    info = tarfile.TarInfo(name=file_entry.path)
                    info.size = len(content_bytes)
                    info.mode = file_entry.mode
                    tar.addfile(info, io.BytesIO(content_bytes))
                    exported.append(file_entry.path)
                else:
                    failed.append(file_entry.path)

        tag = snapshot.metadata.tag or str(snapshot.metadata.id)
        return {
            'snapshot': tag,
            'format': 'tar.gz',
            'output_path': str(output_path),
            'exported_count': len(exported),
            'failed_count': len(failed),
            'archive_size': output_path.stat().st_size if output_path.exists() else 0,
            'files_exported': exported,
            'files_failed': failed
        }

    # ────────────────────────────────────────────
    # Diff & cleanup
    # ────────────────────────────────────────────

    def delete_snapshot(self, snapshot_ref: str) -> bool:
        """Delete a snapshot"""
        snapshot = self.get_snapshot(snapshot_ref)
        if not snapshot or not snapshot.metadata.id:
            return False

        self.store.delete_snapshot(snapshot.metadata.id)
        return True

    def diff_snapshots(
        self,
        from_ref: str,
        to_ref: str = "current",
        file_filters: Optional[List[str]] = None
    ) -> SnapshotDiff:
        """
        Compare two snapshots

        Args:
            from_ref: Source snapshot (ID or tag)
            to_ref: Target snapshot (ID, tag, or 'current')
            file_filters: Optional list of glob patterns to filter diff results

        Returns:
            Diff between snapshots
        """
        # Get source snapshot
        from_snapshot = self.get_snapshot(from_ref)
        if not from_snapshot:
            raise ValueError(f"Snapshot '{from_ref}' not found")

        # Get target snapshot or current state
        if to_ref == "current":
            # Scan current state
            current_files = self.scanner.scan()
            to_files = {f.path: f for f in current_files}
            to_id = 0  # Special ID for current
        else:
            to_snapshot = self.get_snapshot(to_ref)
            if not to_snapshot:
                raise ValueError(f"Snapshot '{to_ref}' not found")
            to_files = {f.path: f for f in to_snapshot.files}
            to_id = to_snapshot.metadata.id or 0

        from_files = {f.path: f for f in from_snapshot.files}

        # Calculate diff
        diff = SnapshotDiff(
            from_snapshot=from_snapshot.metadata.id or 0,
            to_snapshot=to_id
        )

        # Find added files
        diff.files_added = [
            path for path in to_files.keys()
            if path not in from_files
        ]

        # Find removed files
        diff.files_removed = [
            path for path in from_files.keys()
            if path not in to_files
        ]

        # Find modified files
        for path in from_files.keys():
            if path in to_files:
                if from_files[path].hash != to_files[path].hash:
                    diff.files_modified.append(
                        DiffEntry(
                            file_path=path,
                            status='modified',
                            old_hash=from_files[path].hash,
                            new_hash=to_files[path].hash
                        )
                    )

        diff.total_changes = (
            len(diff.files_added) +
            len(diff.files_removed) +
            len(diff.files_modified)
        )

        # Calculate significance score
        total_files = max(len(from_files), len(to_files), 1)
        diff.significance_score = diff.total_changes / total_files

        # Apply file filters if provided
        if file_filters:
            diff = diff.filter_by_paths(file_filters)

        return diff

    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Clean up old autosaves"""
        return self.store.cleanup_old_autosaves(max_keep)

    def cleanup_expired_autosaves(self, delete_after_days: int) -> int:
        """Clean up expired autosaves"""
        return self.store.db.cleanup_expired_autosaves(delete_after_days)

    def cleanup_orphaned_contents(self) -> int:
        """Clean up orphaned file contents from the database"""
        return self.store.db.cleanup_orphaned_contents()

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get the history of a specific file across all snapshots.
        
        Returns a list of entries with snapshot info and whether the file changed.
        """
        # list_snapshots returns List[SnapshotMetadata] objects
        snapshots = self.store.list_snapshots(include_autosave=True)
        history = []
        prev_hash = None

        # Sort snapshots by ID to ensure chronological order
        snapshots.sort(key=lambda s: s.id)

        for snap in snapshots:
            snapshot = self.store.get_snapshot(snap.id)
            if not snapshot:
                continue

            file_entry = snapshot.get_file(file_path)
            if file_entry:
                current_hash = file_entry.hash
                changed = prev_hash is not None and current_hash != prev_hash
                first_seen = prev_hash is None

                history.append({
                    'snapshot_id': snap.id,
                    'tag': snap.tag or '',
                    'date': snap.created_at.isoformat() if hasattr(snap.created_at, 'isoformat') else str(snap.created_at),
                    'message': snap.message or '',
                    'hash': current_hash,
                    'size': file_entry.size,
                    'changed': changed,
                    'first_seen': first_seen
                })
                prev_hash = current_hash
            else:
                if prev_hash is not None:
                    # File existed before but was removed in this snapshot
                    history.append({
                        'snapshot_id': snap.id,
                        'tag': snap.tag or '',
                        'date': snap.created_at.isoformat() if hasattr(snap.created_at, 'isoformat') else str(snap.created_at),
                        'message': snap.message or '',
                        'hash': None,
                        'size': 0,
                        'changed': True,
                        'removed': True
                    })
                    prev_hash = None

        return history

    def search_in_snapshots(
        self,
        query: str,
        file_filter: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for text content across snapshots.
        
        Args:
            query: Text to search for
            file_filter: Optional glob pattern to filter files
            snapshot_ref: Optional snapshot to search in (default: all)
            case_sensitive: Case-sensitive search
        """
        import fnmatch
        results = []
        search_query = query if case_sensitive else query.lower()

        if snapshot_ref:
            # Resolve single snapshot
            snap = self.get_snapshot(snapshot_ref)
            if not snap:
                return []
            snapshots_to_search = [snap.metadata]
        else:
            snapshots_to_search = self.store.list_snapshots(include_autosave=False)

        seen_hashes = set()  # Avoid searching same content twice

        for snap_meta in snapshots_to_search:
            snapshot = self.store.get_snapshot(snap_meta.id)
            if not snapshot:
                continue

            for file_entry in snapshot.files:
                # Apply file filter
                if file_filter and not fnmatch.fnmatch(file_entry.path, file_filter):
                    continue

                # Skip already-searched content
                if file_entry.hash in seen_hashes:
                    continue
                seen_hashes.add(file_entry.hash)

                try:
                    # Get content directly
                    compressed = self.store.db.get_content(file_entry.hash)
                    if not compressed:
                        continue
                    content = self.store.compressor.decompress(compressed).decode('utf-8', errors='replace')
                    search_content = content if case_sensitive else content.lower()

                    if search_query in search_content:
                        # Find matching lines
                        matches = []
                        for i, line in enumerate(content.splitlines(), 1):
                            line_search = line if case_sensitive else line.lower()
                            if search_query in line_search:
                                matches.append({'line': i, 'content': line.strip()})
                                if len(matches) >= 5:  # Cap at 5 matches per file
                                    break

                        results.append({
                            'snapshot_id': snap_meta.id,
                            'tag': snap_meta.tag or '',
                            'file_path': file_entry.path,
                            'matches': matches,
                            'total_matches': sum(
                                1 for l in content.splitlines()
                                if search_query in (l if case_sensitive else l.lower())
                            )
                        })
                except Exception:
                    continue

                if len(results) >= 50:  # Cap total results
                    return results

        return results

    def generate_changelog(
        self,
        from_ref: str,
        to_ref: Optional[str] = None
    ) -> str:
        """
        Generate a Keep-a-Changelog formatted changelog between two snapshots.
        
        Args:
            from_ref: Source snapshot ID or tag
            to_ref: Target snapshot ID or tag (default: latest)
        """
        diff = self.diff_snapshots(from_ref, to_ref or 'current')

        # Get snapshot info for header
        from_snap = self.get_snapshot(from_ref)
        from_meta = from_snap.metadata if from_snap else None
        
        if to_ref and to_ref != 'current':
            to_snap = self.get_snapshot(to_ref)
            to_meta = to_snap.metadata if to_snap else None
            
            to_label = to_meta.tag if to_meta and to_meta.tag else f"Snapshot #{to_meta.id if to_meta else '?'}"
            to_date = to_meta.created_at.strftime("%Y-%m-%d") if to_meta else ""
        else:
            to_label = "current"
            to_date = datetime.now().strftime("%Y-%m-%d")

        from_label = from_meta.tag if from_meta and from_meta.tag else f"Snapshot #{from_meta.id if from_meta else from_ref}"

        lines = []
        lines.append(f"## [{to_label}] - {to_date}")
        lines.append(f"*Compared to {from_label}*")
        lines.append("")

        if diff.files_added:
            lines.append("### Added")
            for path in sorted(diff.files_added):
                lines.append(f"- `{path}`")
            lines.append("")

        if diff.files_modified:
            lines.append("### Changed")
            for entry in sorted(diff.files_modified, key=lambda e: e.file_path):
                lines.append(f"- `{entry.file_path}`")
            lines.append("")

        if diff.files_removed:
            lines.append("### Removed")
            for path in sorted(diff.files_removed):
                lines.append(f"- ~~`{path}`~~")
            lines.append("")

        # Summary line
        total = diff.total_changes
        lines.append(f"---")
        lines.append(f"*{len(diff.files_added)} added, {len(diff.files_modified)} changed, {len(diff.files_removed)} removed ({total} total changes, {diff.significance_score:.0%} significance)*")

        return "\n".join(lines)

```

### 📄 `gencodedoc/mcp/__init__.py`

```python
"""MCP (Model Context Protocol) server implementation"""
from .server import create_app
from .tools import get_tools_definition

__all__ = ["create_app", "get_tools_definition"]

```

### 📄 `gencodedoc/mcp/server.py`

```python
"""MCP server implementation using FastAPI"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..core.config import ConfigManager
from ..core.versioning import VersionManager
from ..core.documentation import DocumentationGenerator
from .tools import get_tools_definition, execute_tool


class ToolRequest(BaseModel):
    """MCP tool request"""
    tool: str
    parameters: Dict[str, Any]


class ToolResponse(BaseModel):
    """MCP tool response"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


def create_app(project_path: Path = Path.cwd()) -> FastAPI:
    """Create FastAPI app for MCP server"""

    app = FastAPI(
        title="GenCodeDoc MCP Server",
        description="Smart documentation and versioning via MCP",
        version="2.0.0"
    )

    # CORS for Claude Desktop
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ NOUVEAU: Cache des managers et autosave
    _managers_cache = {}
    _autosave_managers = {}

    def _get_managers(proj_path: Optional[Path] = None):
        """Get or create managers for a project path"""
        if proj_path is None:
            proj_path = project_path

        proj_path = Path(proj_path).resolve()
        path_str = str(proj_path)

        if path_str not in _managers_cache:
            config_manager = ConfigManager(proj_path)
            config = config_manager.load()
            version_manager = VersionManager(config)
            doc_generator = DocumentationGenerator(config)

            _managers_cache[path_str] = {
                'config': config,
                'version_manager': version_manager,
                'doc_generator': doc_generator
            }

        return _managers_cache[path_str]

    # ✅ NOUVEAU: Classe simple pour autosave
    class AutosaveHelper:
        @staticmethod
        def start(proj_path: Path, mode: Optional[str] = None):
            from ..core.autosave import AutosaveManager

            managers = _get_managers(proj_path)
            config = managers['config']
            version_manager = managers['version_manager']

            if mode:
                config.autosave.mode = mode
            config.autosave.enabled = True

            autosave = AutosaveManager(config, version_manager)
            autosave.start()

            path_str = str(proj_path.resolve())
            _autosave_managers[path_str] = autosave

            return {
                "project": str(proj_path),
                "mode": config.autosave.mode,
                "status": "running"
            }

        @staticmethod
        def stop(proj_path: Path):
            path_str = str(proj_path.resolve())
            if path_str in _autosave_managers:
                _autosave_managers[path_str].stop()
                del _autosave_managers[path_str]
                return {"status": "stopped"}
            return {"status": "not_running"}

        @staticmethod
        def get_status():
            return [
                {
                    "project": path,
                    "status": "running",
                    "last_save": mgr.last_save.isoformat() if mgr.last_save else None
                }
                for path, mgr in _autosave_managers.items()
            ]

    autosave_helper = AutosaveHelper()

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "GenCodeDoc MCP Server",
            "version": "2.0.0",
            "project": project_path.name,
            "endpoints": {
                "tools": "/mcp/tools",
                "execute": "/mcp/execute"
            }
        }

    @app.get("/mcp/tools")
    async def list_tools():
        """List available tools"""
        return {"tools": get_tools_definition()}

    @app.post("/mcp/execute", response_model=ToolResponse)
    async def execute(request: ToolRequest):
        """Execute a tool"""
        try:
            # Extraire project_path des paramètres
            proj_path = request.parameters.pop("project_path", None)

            managers = _get_managers(proj_path)

            result = execute_tool(
                tool_name=request.tool,
                parameters=request.parameters,
                version_manager=managers['version_manager'],
                doc_generator=managers['doc_generator'],
                config=managers['config'],
                server=autosave_helper  # ✅ NOUVEAU
            )

            return ToolResponse(success=True, result=result)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        for autosave in _autosave_managers.values():
            autosave.stop()
        _autosave_managers.clear()

    return app

```

### 📄 `gencodedoc/mcp/server_sse.py`

```python
"""MCP server with SSE transport - Native implementation"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any
import time

from ..core.config import ConfigManager
from ..core.versioning import VersionManager
from ..core.documentation import DocumentationGenerator
from .tools import get_tools_definition, execute_tool


class MCPSSEServer:
    """MCP Server with SSE transport"""

    def __init__(self, project_path: Path):
        self.project_path = project_path

        # Initialize managers
        config_manager = ConfigManager(project_path)
        self.config = config_manager.load()
        self.version_manager = VersionManager(self.config)
        self.doc_generator = DocumentationGenerator(self.config)

        # Store active connections
        self.connections = set()

        # ✅ NOUVEAU: Cache des managers par projet
        self._managers_cache = {}

        # ✅ NOUVEAU: Autosave managers
        self._autosave_managers = {}

    def _get_managers(self, project_path: Optional[Path] = None):
        """Get or create managers for a project path"""
        if project_path is None:
            project_path = self.project_path

        project_path = Path(project_path).resolve()
        path_str = str(project_path)

        if path_str not in self._managers_cache:
            config_manager = ConfigManager(project_path)
            config = config_manager.load()
            version_manager = VersionManager(config)
            doc_generator = DocumentationGenerator(config)

            self._managers_cache[path_str] = {
                'config': config,
                'version_manager': version_manager,
                'doc_generator': doc_generator
            }

        return self._managers_cache[path_str]

    # ═══════════════════════════════════════════════════════════
    # AUTOSAVE MANAGEMENT (identique à server_stdio.py)
    # ═══════════════════════════════════════════════════════════

    def start_autosave(self, project_path: Path, mode: Optional[str] = None) -> dict:
        """Start autosave for a project"""
        from ..core.autosave import AutosaveManager

        managers = self._get_managers(project_path)
        config = managers['config']
        version_manager = managers['version_manager']

        if mode:
            config.autosave.mode = mode

        config.autosave.enabled = True

        autosave = AutosaveManager(config, version_manager)
        autosave.start()

        path_str = str(project_path.resolve())
        self._autosave_managers[path_str] = autosave

        return {
            "project": str(project_path),
            "mode": config.autosave.mode,
            "status": "running"
        }

    def stop_autosave(self, project_path: Path) -> dict:
        """Stop autosave for a project"""
        path_str = str(project_path.resolve())
        if path_str in self._autosave_managers:
            self._autosave_managers[path_str].stop()
            del self._autosave_managers[path_str]
            return {"status": "stopped"}
        return {"status": "not_running"}

    def get_autosave_status(self) -> list:
        """Get status of all autosaves"""
        return [
            {
                "project": path,
                "status": "running",
                "last_save": mgr.last_save.isoformat() if mgr.last_save else None
            }
            for path, mgr in self._autosave_managers.items()
        ]

    async def shutdown(self):
        """Cleanup on server shutdown"""
        for autosave in self._autosave_managers.values():
            autosave.stop()
        self._autosave_managers.clear()

    # ═══════════════════════════════════════════════════════════
    # REQUEST HANDLING
    # ═══════════════════════════════════════════════════════════

    async def handle_request(self, request: dict) -> Optional[dict]:
        """Handle MCP request - Returns None for notifications"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # ✅ NOUVEAU: Détecter si c'est une notification (pas d'id)
        is_notification = request_id is None

        try:
            # ✅ CORRECTION: Extraire project_path SAUF pour les outils qui en ont besoin
            project_path = None

            # ✅ NOUVEAU: Liste des outils qui ont BESOIN de project_path comme paramètre
            TOOLS_REQUIRING_PROJECT_PATH = {
                "init_project",
                "start_autosave",
                "stop_autosave"
            }

            if method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if isinstance(tool_args, dict):
                    # ✅ CORRECTION: Ne pop que si l'outil n'en a pas besoin
                    if tool_name not in TOOLS_REQUIRING_PROJECT_PATH:
                        project_path = tool_args.pop("project_path", None)
                    else:
                        # Juste extraire sans supprimer
                        project_path = tool_args.get("project_path")

            elif isinstance(params, dict):
                # Pour les appels directs
                project_path = params.pop("project_path", None)

            # Obtenir les managers
            managers = self._get_managers(project_path)
            version_manager = managers['version_manager']
            doc_generator = managers['doc_generator']
            config = managers['config']

            tool_names = [t["name"] for t in get_tools_definition()]

            # === DISPATCH ===

            if method == "tools/list":
                result = {"tools": get_tools_definition()}

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_params = params.get("arguments", {})

                result = execute_tool(
                    tool_name=tool_name,
                    parameters=tool_params,
                    version_manager=version_manager,
                    doc_generator=doc_generator,
                    config=config,
                    server=self
                )

            elif method in tool_names:
                result = execute_tool(
                    tool_name=method,
                    parameters=params,
                    version_manager=version_manager,
                    doc_generator=doc_generator,
                    config=config,
                    server=self
                )

            elif method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "gencodedoc",
                        "version": "2.0.0"
                    }
                }

            # ✅ NOUVEAU: 5. Notifications (à ignorer)
            elif method and method.startswith("notifications/"):
                if is_notification:
                    return None
                else:
                    result = {}

            else:
                if is_notification:
                    return None

                raise ValueError(f"Unknown method: {method}")

            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request_id or 0,
                "result": result
            }

        except Exception as e:
            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request_id or 0,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


def create_sse_app(project_path: Path = Path.cwd()) -> FastAPI:
    """Create FastAPI app with SSE endpoint for MCP"""

    app = FastAPI(
        title="GenCodeDoc MCP Server (SSE)",
        description="Smart documentation and versioning via MCP SSE",
        version="2.0.0"
    )

    mcp_server = MCPSSEServer(project_path)

    async def sse_event_stream(request: Request) -> AsyncGenerator:
        """Generate SSE events"""

        # Format SSE message
        def format_sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        try:
            # Send initial connection event
            yield format_sse("connected", {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "gencodedoc",
                    "version": "2.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            })

            # Keep connection alive with heartbeat
            while True:
                # Check if client is still connected
                if await request.is_disconnected():
                    break

                # Send heartbeat every 30 seconds
                yield format_sse("heartbeat", {
                    "timestamp": time.time(),
                    "status": "alive"
                })

                await asyncio.sleep(30)

        except asyncio.CancelledError:
            pass

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "GenCodeDoc MCP Server (SSE)",
            "version": "2.0.0",
            "transport": "sse",
            "endpoints": {
                "sse": "/mcp/sse",
                "tools": "/mcp/tools",
                "call": "/mcp/call"
            }
        }

    @app.get("/mcp/sse")
    async def mcp_sse_endpoint(request: Request):
        """SSE endpoint for MCP protocol"""
        return StreamingResponse(
            sse_event_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    @app.get("/mcp/tools")
    async def list_tools():
        """List available MCP tools"""
        return {"tools": get_tools_definition()}

    @app.post("/mcp/call")
    async def call_tool(request: dict):
        """Call an MCP tool"""
        response = await mcp_server.handle_request(request)
        # ✅ NOUVEAU: Ne retourner que si pas None
        return response if response is not None else {}

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        await mcp_server.shutdown()

    return app


async def main():
    """Main entry point for SSE server"""
    import os
    import uvicorn

    project_path = Path(os.getenv("PROJECT_PATH", Path.cwd()))
    app = create_sse_app(project_path)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

```



---
**🚀 Suite dans la partie suivante...**