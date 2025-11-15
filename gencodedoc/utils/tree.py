"""Directory tree generation"""
from pathlib import Path
from typing import Optional, Set, Callable

class TreeGenerator:
    """Generate directory tree visualization"""

    def __init__(self, show_hidden: bool = False):
        self.show_hidden = show_hidden

    def generate(
        self,
        root: Path,
        prefix: str = '',
        is_last: bool = True,
        max_depth: Optional[int] = None,
        current_depth: int = 0,
        filter_func: Optional[Callable] = None
    ) -> str:
        """Generate tree structure"""
        if max_depth is not None and current_depth >= max_depth:
            return ''

        tree = ''
        basename = root.name

        if current_depth == 0:
            tree += f"{basename}\n"
        else:
            tree += prefix + ('└── ' if is_last else '├── ') + basename + '\n'

        try:
            items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            if not self.show_hidden:
                items = [i for i in items if not i.name.startswith('.')]

            if filter_func:
                items = [i for i in items if filter_func(i)]

            for index, item in enumerate(items):
                is_last_item = index == len(items) - 1

                if current_depth == 0:
                    new_prefix = ''
                else:
                    new_prefix = prefix + ('    ' if is_last else '│   ')

                if item.is_dir():
                    tree += self.generate(
                        item,
                        new_prefix,
                        is_last_item,
                        max_depth,
                        current_depth + 1,
                        filter_func
                    )
                else:
                    tree += new_prefix + ('└── ' if is_last_item else '├── ') + item.name + '\n'

        except PermissionError:
            pass

        return tree

    def generate_with_selection(
        self,
        root: Path,
        selected_paths: Set[Path],
        filter_func: Optional[Callable] = None
    ) -> str:
        """Generate tree showing all structure but marking selected files"""
        return self._generate_marked(root, selected_paths, '', True, filter_func)

    def _generate_marked(
        self,
        root: Path,
        selected: Set[Path],
        prefix: str,
        is_last: bool,
        filter_func: Optional[Callable]
    ) -> str:
        """Internal method for marked tree generation"""
        tree = ''
        basename = root.name

        marker = ' ✓' if root in selected else ''

        if prefix == '':
            tree += f"{basename}{marker}\n"
        else:
            tree += prefix + ('└── ' if is_last else '├── ') + basename + marker + '\n'

        try:
            items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            if not self.show_hidden:
                items = [i for i in items if not i.name.startswith('.')]

            if filter_func:
                items = [i for i in items if filter_func(i)]

            for index, item in enumerate(items):
                is_last_item = index == len(items) - 1
                new_prefix = prefix + ('    ' if is_last else '│   ')

                if item.is_dir():
                    tree += self._generate_marked(
                        item, selected, new_prefix, is_last_item, filter_func
                    )
                else:
                    marker = ' ✓' if item in selected else ''
                    tree += new_prefix + ('└── ' if is_last_item else '├── ') + item.name + marker + '\n'

        except PermissionError:
            pass

        return tree
