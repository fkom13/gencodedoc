"""Documentation generation (port from JS)"""
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
from ..models.config import ProjectConfig
from ..utils.tree import TreeGenerator
from ..utils.formatters import get_language_from_extension
from ..utils.filters import FileFilter

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
        tree_full_code_select: Optional[bool] = None
    ) -> Path:
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
            output_path = self._generate_output_path()

        # Collect files
        files = self._collect_files(include_paths, exclude_paths)

        # Build markdown
        markdown = self._build_markdown(
            files=files,
            include_tree=include_tree,
            include_code=include_code,
            tree_full_code_select=tree_full_code_select
        )

        # Write
        output_path.write_text(markdown, encoding='utf-8')

        return output_path

    def _generate_output_path(self) -> Path:
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
                if path.is_file():
                    files.append(path)
                elif path.is_dir():
                    files.extend(self.filter.scan_directory(path))
        else:
            files = self.filter.scan_directory(self.config.project_path)

        # Apply exclusions
        if exclude_paths:
            exclude_set = {self.config.project_path / p for p in exclude_paths}
            files = [f for f in files if f not in exclude_set]

        # Filter by max size
        max_size = self.config.output.max_file_size
        files = [f for f in files if f.stat().st_size <= max_size]

        return sorted(files)

    def _build_markdown(
        self,
        files: List[Path],
        include_tree: bool,
        include_code: bool,
        tree_full_code_select: bool
    ) -> str:
        """Build markdown content"""
        md = []

        # Header
        project_name = self.config.project_name or self.config.project_path.name
        md.append(f"# Documentation du projet: {project_name}\n")
        md.append(f"> Généré le {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

        # Tree
        if include_tree:
            md.append("## 📂 Structure du projet\n\n")
            md.append("```\n")

            if tree_full_code_select and files:
                # Full tree but mark selected
                selected_set = set(files)
                tree = self.tree_gen.generate_with_selection(
                    self.config.project_path,
                    selected_set,
                    lambda p: not self.filter.should_ignore(p, p.is_dir())
                )
            else:
                # Normal tree
                tree = self.tree_gen.generate(
                    self.config.project_path,
                    filter_func=lambda p: not self.filter.should_ignore(p, p.is_dir())
                )

            md.append(tree)
            md.append("```\n\n")

        # File contents
        if include_code:
            md.append("## 📝 Contenu des fichiers\n\n")

            for file_path in files:
                relative_path = file_path.relative_to(self.config.project_path)
                md.append(f"### 📄 `{relative_path}`\n\n")

                try:
                    content = file_path.read_text(encoding='utf-8')

                    if self.config.output.language_detection:
                        lang = get_language_from_extension(str(file_path))
                    else:
                        lang = 'text'

                    md.append(f"```{lang}\n{content}\n```\n\n")

                except Exception as e:
                    md.append(f"```\nErreur lors de la lecture: {e}\n```\n\n")

        return ''.join(md)
