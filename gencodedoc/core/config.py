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
        """Apply preset"""
        presets = {
            'python': {
                'dirs': ['venv', '.venv', '__pycache__', 'dist', 'build'],
                'extensions': ['.pyc', '.pyo', '.pyd']
            },
            'nodejs': {
                'dirs': ['node_modules', 'dist', 'build'],
                'files': ['package-lock.json', 'yarn.lock']
            },
            'web': {
                'dirs': ['node_modules', 'dist'],
                'extensions': ['.map', '.min.js']
            },
            'go': {
                'dirs': ['vendor', 'bin'],
                'extensions': ['.exe']
            }
        }

        if preset in presets:
            p = presets[preset]
            if 'dirs' in p:
                config.ignore.dirs.extend(p['dirs'])
            if 'files' in p:
                config.ignore.files.extend(p['files'])
            if 'extensions' in p:
                config.ignore.extensions.extend(p['extensions'])

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
