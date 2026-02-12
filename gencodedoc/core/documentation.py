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
