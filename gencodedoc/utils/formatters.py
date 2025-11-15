"""Formatting utilities"""
from datetime import datetime
from typing import Union

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_date(dt: Union[datetime, str], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(fmt)


def get_language_from_extension(file_path: str) -> str:
    """Get language identifier for syntax highlighting"""
    import os
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'jsx',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.sql': 'sql',
        '.r': 'r',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.dart': 'dart',
    }

    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path).lower()

    if filename == 'dockerfile':
        return 'dockerfile'
    if filename == 'makefile':
        return 'makefile'

    return ext_map.get(ext, 'text')
