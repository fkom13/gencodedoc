"""Configuration models using Pydantic"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional
from pathlib import Path

class IgnoreConfig(BaseModel):
    """File/directory ignore configuration"""
    dirs: List[str] = Field(default_factory=lambda: [
        'node_modules', 'venv', '.venv', 'env', '__pycache__',
        '.git', 'dist', 'build', '.next', 'coverage'
    ])
    files: List[str] = Field(default_factory=lambda: [
        '.DS_Store', 'Thumbs.db', 'package-lock.json', 'yarn.lock'
    ])
    extensions: List[str] = Field(default_factory=lambda: [
        '.log', '.pyc', '.pyo', '.exe', '.bin',
        '.jpg', '.png', '.gif', '.mp4', '.pdf', '.zip'
    ])
    patterns: List[str] = Field(default_factory=list)

class TimerConfig(BaseModel):
    """Timer-based autosave"""
    interval: int = Field(default=300, description="Interval in seconds")

class DiffThresholdConfig(BaseModel):
    """Diff threshold autosave"""
    threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    check_interval: int = Field(default=60)
    ignore_whitespace: bool = True
    ignore_comments: bool = False

class HybridAutosaveConfig(BaseModel):
    """Hybrid autosave (timer OR threshold)"""
    min_interval: int = Field(default=180)
    max_interval: int = Field(default=600)
    threshold: float = Field(default=0.03, ge=0.0, le=1.0)

class RetentionConfig(BaseModel):
    """Snapshot retention policy"""
    max_autosaves: int = Field(default=50, ge=1)
    compress_after_days: int = Field(default=7, ge=0)
    delete_after_days: int = Field(default=30, ge=0)
    keep_manual: bool = True

class AutosaveConfig(BaseModel):
    """Autosave configuration"""
    enabled: bool = False
    mode: Literal['timer', 'diff', 'hybrid'] = 'hybrid'
    timer: TimerConfig = Field(default_factory=TimerConfig)
    diff_threshold: DiffThresholdConfig = Field(default_factory=DiffThresholdConfig)
    hybrid: HybridAutosaveConfig = Field(default_factory=HybridAutosaveConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)

class DiffFormatConfig(BaseModel):
    """Diff output format"""
    default: Literal['unified', 'json', 'ast'] = 'unified'
    unified_context: int = Field(default=3, ge=0)
    json_include_content: bool = True
    ast_enabled: bool = False

class OutputConfig(BaseModel):
    """Documentation output settings"""
    default_name: str = "{project}_doc_{date}.md"
    include_tree: bool = True
    include_code: bool = True
    tree_full_code_select: bool = False
    language_detection: bool = True
    max_file_size: int = Field(default=1_000_000, ge=0)

class ProjectConfig(BaseModel):
    """Main project configuration"""
    model_config = ConfigDict(extra='allow')
    
    project_name: str = ""
    project_path: Path

    ignore: IgnoreConfig = Field(default_factory=IgnoreConfig)
    autosave: AutosaveConfig = Field(default_factory=AutosaveConfig)
    diff_format: DiffFormatConfig = Field(default_factory=DiffFormatConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    storage_path: Path = Field(default=Path(".gencodedoc"))
    compression_enabled: bool = True
    compression_level: int = Field(default=3, ge=1, le=22)
