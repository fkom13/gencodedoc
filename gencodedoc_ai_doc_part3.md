# gencodedoc (Partie 3)
> Suite de la documentation (12/02/2026)

### 📄 `gencodedoc/mcp/server_stdio.py`

```python
"""MCP server with stdio transport for CLI integration"""
import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
import os

from ..core.config import ConfigManager
from ..core.versioning import VersionManager
from ..core.documentation import DocumentationGenerator
from .tools import get_tools_definition, execute_tool


class MCPStdioServer:
    """MCP Server using stdio transport"""

    def __init__(self, default_project_path: Path):
        self.default_project_path = default_project_path

        # Cache des managers par projet
        self._managers_cache = {}

        # ✅ NOUVEAU: Autosave managers par projet
        self._autosave_managers = {}

    def _get_managers(self, project_path: Optional[Path] = None):
        """Get or create managers for a project path"""
        if project_path is None:
            project_path = self.default_project_path

        # Normaliser le path
        project_path = Path(project_path).resolve()
        path_str = str(project_path)

        # Vérifier le cache
        if path_str not in self._managers_cache:
            # Créer les managers
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
    # AUTOSAVE MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def start_autosave(self, project_path: Path, mode: Optional[str] = None) -> dict:
        """Start autosave for a project"""
        from ..core.autosave import AutosaveManager

        managers = self._get_managers(project_path)
        config = managers['config']
        version_manager = managers['version_manager']

        # Update config mode if provided
        if mode:
            config.autosave.mode = mode

        # Enable autosave
        config.autosave.enabled = True

        # Create and start
        autosave = AutosaveManager(config, version_manager)
        autosave.start()

        # Store
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

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                # Pour les appels directs, project_path est dans params
                project_path = params.pop("project_path", None)

            # Obtenir les managers (créés dynamiquement ou depuis cache)
            managers = self._get_managers(project_path)
            version_manager = managers['version_manager']
            doc_generator = managers['doc_generator']
            config = managers['config']

            # Liste des noms d'outils disponibles
            tool_names = [t["name"] for t in get_tools_definition()]

            # === DISPATCH ===

            # 1. Liste des outils
            if method == "tools/list":
                result = {"tools": get_tools_definition()}

            # 2. Appel MCP standard : tools/call avec {name, arguments}
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

            # 3. Appel direct gemini-cli : nom de l'outil comme method
            elif method in tool_names:
                result = execute_tool(
                    tool_name=method,
                    parameters=params,
                    version_manager=version_manager,
                    doc_generator=doc_generator,
                    config=config,
                    server=self
                )

            # 4. Initialisation
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
                # C'est une notification, on l'ignore silencieusement
                if is_notification:
                    return None
                else:
                    # Si elle a un id (erreur du client), retourner vide
                    result = {}

            # 6. Méthode inconnue
            else:
                # ✅ NOUVEAU: Si c'est une notification inconnue, ignorer
                if is_notification:
                    return None

                raise ValueError(f"Unknown method: {method}")

            # ✅ NOUVEAU: Ne pas retourner de réponse pour les notifications
            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request_id or 0,
                "result": result
            }

        except Exception as e:
            # ✅ NOUVEAU: Ne pas retourner d'erreur pour les notifications
            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request_id or 0,
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": {
                        "traceback": str(e.__class__.__name__)
                    }
                }
            }

    async def run(self):
        """Run the stdio server"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # === CORRECTION : Extraire l'ID AVANT ===
                request_id = None
                try:
                    request = json.loads(line)
                    request_id = request.get("id")

                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue

                # === Handle request ===
                try:
                    response = await self.handle_request(request)

                    # ✅ NOUVEAU: Ne pas imprimer si c'est None (notification)
                    if response is not None:
                        print(json.dumps(response), flush=True)

                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id or 0,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {
                        "code": -32603,
                        "message": f"Fatal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


async def main():
    """Main entry point"""
    project_path = Path(os.getenv("PROJECT_PATH", Path.cwd()))

    server = MCPStdioServer(project_path)

    try:
        await server.run()
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

```

### 📄 `gencodedoc/mcp/tools.py`

```python
"""MCP tools definition and execution"""
from typing import Any, Dict, List, Optional
from pathlib import Path


def get_tools_definition() -> List[Dict[str, Any]]:
    """Get MCP tools definition"""
    return [
        # ═══════════════════════════════════════════════════════════
        # SNAPSHOT MANAGEMENT
        # ═══════════════════════════════════════════════════════════
        {
            "name": "create_snapshot",
            "description": "Create a snapshot of the current project state",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional commit message"
                    },
                    "tag": {
                        "type": "string",
                        "description": "Optional tag for easy reference"
                    },
                    "include_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific paths to include"
                    }
                }
            }
        },
        {
            "name": "list_snapshots",
            "description": "List all snapshots",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of snapshots to return",
                        "default": 10
                    },
                    "include_autosave": {
                        "type": "boolean",
                        "description": "Include autosave snapshots",
                        "default": False
                    }
                }
            }
        },
        {
            "name": "get_snapshot_details",
            "description": "Get detailed information about a specific snapshot",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag"
                    }
                },
                "required": ["snapshot_ref"]
            }
        },
        {
            "name": "restore_snapshot",
            "description": "Restore a previous snapshot (full or partial via file_filters)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag to restore"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Overwrite existing files",
                        "default": False
                    },
                    "file_filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Glob patterns or paths to restore selectively (partial restore)"
                    }
                },
                "required": ["snapshot_ref"]
            }
        },
        {
            "name": "delete_snapshot",
            "description": "Delete a snapshot permanently",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag to delete"
                    }
                },
                "required": ["snapshot_ref"]
            }
        },
        {
            "name": "diff_versions",
            "description": "Compare two versions, optionally filtered to specific files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "from_ref": {
                        "type": "string",
                        "description": "Source snapshot ID or tag"
                    },
                    "to_ref": {
                        "type": "string",
                        "description": "Target snapshot ID, tag, or 'current'",
                        "default": "current"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["unified", "json", "markdown"],
                        "description": "Diff output format",
                        "default": "unified"
                    },
                    "file_filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Glob patterns or paths to filter diff results"
                    }
                },
                "required": ["from_ref"]
            }
        },

        # ═══════════════════════════════════════════════════════════
        # DOCUMENTATION
        # ═══════════════════════════════════════════════════════════
        {
            "name": "generate_documentation",
            "description": "Generate project documentation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output file path"
                    },
                    "include_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific paths to include"
                    },
                    "include_tree": {
                        "type": "boolean",
                        "description": "Include directory tree",
                        "default": True
                    },
                    "include_code": {
                        "type": "boolean",
                        "description": "Include file code",
                        "default": True
                    },
                    "split_limit": {
                        "type": "integer",
                        "description": "Split output into multiple files if line count exceeds this limit"
                    },
                    "ignore_tree_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Patterns to exclude from the directory tree view (e.g. ['*.jpg', 'node_modules'])"
                    }
                }
            }
        },
        {
            "name": "preview_structure",
            "description": "Preview project directory structure",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum tree depth"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination",
                        "default": 1
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Lines per page",
                        "default": 50
                    },
                    "ignore_add": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ad-hoc ignore patterns (e.g. ['node_modules', '*.log'])"
                    }
                }
            }
        },
        {
            "name": "get_project_stats",
            "description": "Get project statistics",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                }
            }
        },
        # ═══════════════════════════════════════════════════════════
        # CODE INTELLIGENCE
        # ═══════════════════════════════════════════════════════════
        {
            "name": "get_file_history",
            "description": "Track the history of a specific file across all snapshots",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path of the file to track"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "search_snapshots",
            "description": "Search for text content across snapshots",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "file_filter": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g. '*.py')"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Search in specific snapshot only"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Case-sensitive search",
                        "default": False
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "generate_changelog",
            "description": "Generate a Keep-a-Changelog formatted changelog between two snapshots",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "from_ref": {
                        "type": "string",
                        "description": "Source snapshot ID or tag"
                    },
                    "to_ref": {
                        "type": "string",
                        "description": "Target snapshot ID, tag, or 'current'",
                        "default": "current"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                },
                "required": ["from_ref"]
            }
        },

        # ═══════════════════════════════════════════════════════════
        # PROJECT MANAGEMENT
        # ═══════════════════════════════════════════════════════════
        {
            "name": "init_project",
            "description": "Initialize gencodedoc for a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "preset": {
                        "type": "string",
                        "enum": ["python", "nodejs", "web", "go"],
                        "description": "Configuration preset"
                    }
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "get_project_status",
            "description": "Get current project status and configuration",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                }
            }
        },

        # ═══════════════════════════════════════════════════════════
        # CONFIGURATION
        # ═══════════════════════════════════════════════════════════
        {
            "name": "get_config",
            "description": "Get project configuration",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                }
            }
        },
        {
            "name": "set_config_value",
            "description": "Set a configuration value",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "key": {
                        "type": "string",
                        "description": "Config key (e.g., 'autosave.enabled')"
                    },
                    "value": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "boolean"}
                        ],
                        "description": "Value to set (string, number, or boolean)"
                    }
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "apply_preset",
            "description": "Apply a configuration preset",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "preset": {
                        "type": "string",
                        "enum": ["python", "nodejs", "web", "go"],
                        "description": "Preset name"
                    }
                },
                "required": ["preset"]
            }
        },
        {
            "name": "manage_ignore_rules",
            "description": "Manage file/directory ignore rules",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "add_dir": {
                        "type": "string",
                        "description": "Add directory to ignore"
                    },
                    "add_file": {
                        "type": "string",
                        "description": "Add file to ignore"
                    },
                    "add_ext": {
                        "type": "string",
                        "description": "Add extension to ignore"
                    },
                    "list_all": {
                        "type": "boolean",
                        "description": "List all ignore rules",
                        "default": False
                    }
                }
            }
        },

        # ═══════════════════════════════════════════════════════════
        # AUTOSAVE
        # ═══════════════════════════════════════════════════════════
        {
            "name": "start_autosave",
            "description": "Start automatic versioning for a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["timer", "diff", "hybrid"],
                        "description": "Autosave mode",
                        "default": "hybrid"
                    }
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "stop_autosave",
            "description": "Stop automatic versioning for a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project"
                    }
                },
                "required": ["project_path"]
            }
        },
        {
            "name": "get_autosave_status",
            "description": "Get autosave status for all monitored projects",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },

        # ═══════════════════════════════════════════════════════════
        # FILE EXPLORATION & EXPORT (v2.1.0)
        # ═══════════════════════════════════════════════════════════
        {
            "name": "get_file_at_version",
            "description": "View the content of a specific file at a specific snapshot version",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Relative path of the file in the snapshot"
                    }
                },
                "required": ["snapshot_ref", "file_path"]
            }
        },
        {
            "name": "list_files_at_version",
            "description": "List all files present in a specific snapshot version",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files"
                    }
                },
                "required": ["snapshot_ref"]
            }
        },
        {
            "name": "restore_files",
            "description": "Restore specific files from a snapshot (partial restore)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag"
                    },
                    "file_filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Glob patterns or paths to restore selectively"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Overwrite existing files",
                        "default": True
                    }
                },
                "required": ["snapshot_ref", "file_filters"]
            }
        },
        {
            "name": "export_snapshot",
            "description": "Export a snapshot to a folder or .tar.gz archive",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    },
                    "snapshot_ref": {
                        "type": "string",
                        "description": "Snapshot ID or tag to export"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Target folder or archive path"
                    },
                    "archive": {
                        "type": "boolean",
                        "description": "Create a .tar.gz archive instead of folder",
                        "default": False
                    },
                    "file_filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional glob patterns to filter files"
                    }
                },
                "required": ["snapshot_ref", "output_path"]
            }
        },
        {
            "name": "cleanup_orphaned_contents",
            "description": "Remove orphaned file contents no longer referenced by any snapshot",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project (optional)"
                    }
                }
            }
        }
    ]


def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    version_manager,
    doc_generator,
    config,
    server=None  # ✅ Référence au serveur pour autosave et invalidation cache
) -> Any:
    """Execute a tool with given parameters - Returns MCP-compliant format"""

    # ═══════════════════════════════════════════════════════════
    # SNAPSHOT MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    if tool_name == "create_snapshot":
        try:
            snapshot = version_manager.create_snapshot(
                message=parameters.get("message"),
                tag=parameters.get("tag"),
                include_paths=parameters.get("include_paths")
            )

            text = f"""✅ Snapshot created successfully!

📸 Snapshot ID: {snapshot.metadata.id}
🏷️  Tag: {snapshot.metadata.tag or '(no tag)'}
📝 Message: {snapshot.metadata.message or '(no message)'}
📁 Files: {snapshot.metadata.files_count}
💾 Size: {snapshot.metadata.total_size / 1024:.1f} KB
"""

            return {
                "content": [{"type": "text", "text": text}],
                "snapshot_id": snapshot.metadata.id,
                "files_count": snapshot.metadata.files_count,
                "total_size": snapshot.metadata.total_size,
                "tag": snapshot.metadata.tag
            }

        except Exception as e:
            # ✅ NOUVEAU: Message clair pour contrainte unique
            if "UNIQUE constraint failed: snapshots.hash" in str(e):
                text = """ℹ️  No snapshot created - No changes detected

The project state is identical to the last snapshot.
No new snapshot was created to avoid duplication.

💡 Tip: Make some changes to the code before creating a new snapshot.
"""
                return {
                    "content": [{"type": "text", "text": text}],
                    "snapshot_id": None,
                    "reason": "no_changes"
                }
            elif "UNIQUE constraint failed: snapshots.tag" in str(e):
                text = f"""❌ Snapshot creation failed - Tag already exists

The tag '{parameters.get("tag")}' is already used by another snapshot.

💡 Use a different tag or list existing snapshots with:
   list_snapshots
"""
                return {
                    "content": [{"type": "text", "text": text}],
                    "error": "duplicate_tag",
                    "tag": parameters.get("tag")
                }
            else:
                # Autre erreur
                raise

    elif tool_name == "list_snapshots":
        snapshots = version_manager.list_snapshots(
            limit=parameters.get("limit", 10),
            include_autosave=parameters.get("include_autosave", False)
        )

        snapshots_list = [
            {
                "id": s.metadata.id,
                "tag": s.metadata.tag,
                "message": s.metadata.message,
                "created_at": s.metadata.created_at.isoformat(),
                "files_count": s.metadata.files_count,
                "is_autosave": s.metadata.is_autosave
            }
            for s in snapshots
        ]

        # Format texte lisible
        text_lines = [f"📸 Found {len(snapshots_list)} snapshot(s):\n"]

        for s in snapshots_list:
            text_lines.append(f"\n[{s['id']}] {s['tag'] or '(no tag)'}")
            text_lines.append(f"  📝 {s['message'] or '(no message)'}")
            text_lines.append(f"  📅 {s['created_at']}")
            text_lines.append(f"  📁 {s['files_count']} files")
            text_lines.append(f"  🔧 {'Auto' if s['is_autosave'] else 'Manual'}")

        return {
            "content": [{"type": "text", "text": "\n".join(text_lines)}],
            "snapshots": snapshots_list,
            "count": len(snapshots_list)
        }

    elif tool_name == "get_snapshot_details":
        snapshot = version_manager.get_snapshot(parameters["snapshot_ref"])

        if not snapshot:
            return {
                "content": [{"type": "text", "text": f"❌ Snapshot '{parameters['snapshot_ref']}' not found"}],
                "error": "Snapshot not found"
            }

        files_preview = [f.path for f in snapshot.files[:20]]

        text = f"""📸 Snapshot Details

ID: {snapshot.metadata.id}
Tag: {snapshot.metadata.tag or '(no tag)'}
Message: {snapshot.metadata.message or '(no message)'}
Created: {snapshot.metadata.created_at.isoformat()}
Type: {'Autosave' if snapshot.metadata.is_autosave else 'Manual'}
Trigger: {snapshot.metadata.trigger_type}
Files: {snapshot.metadata.files_count}
Total Size: {snapshot.metadata.total_size / 1024:.1f} KB
Compressed: {snapshot.metadata.compressed_size / 1024:.1f} KB

Files (showing first 20):
""" + "\n".join(f"  • {f}" for f in files_preview)

        if len(snapshot.files) > 20:
            text += f"\n  ... and {len(snapshot.files) - 20} more"

        return {
            "content": [{"type": "text", "text": text}],
            "snapshot": {
                "id": snapshot.metadata.id,
                "tag": snapshot.metadata.tag,
                "message": snapshot.metadata.message,
                "created_at": snapshot.metadata.created_at.isoformat(),
                "files_count": snapshot.metadata.files_count,
                "files": [f.path for f in snapshot.files]
            }
        }

    elif tool_name == "restore_snapshot":
        try:
            result = version_manager.restore_snapshot(
                snapshot_ref=parameters["snapshot_ref"],
                force=parameters.get("force", False),
                file_filters=parameters.get("file_filters")
            )

            partial = " (partial)" if parameters.get("file_filters") else ""
            text = f"""✅ Snapshot restored{partial}!

📸 Snapshot: {parameters['snapshot_ref']}
📁 Restored: {result['restored_count']}/{result['total_files']} files
"""
            if result['skipped_count'] > 0:
                text += f"⏭️  Skipped: {result['skipped_count']} files\n"

            return {
                "content": [{"type": "text", "text": text}],
                "success": True,
                **result
            }
        except ValueError as e:
            return {
                "content": [{"type": "text", "text": f"❌ {str(e)}"}],
                "success": False,
                "error": str(e)
            }

    elif tool_name == "delete_snapshot":
        success = version_manager.delete_snapshot(parameters["snapshot_ref"])

        text = f"""{'✅ Snapshot deleted successfully!' if success else '❌ Snapshot not found'}

📸 Snapshot: {parameters['snapshot_ref']}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "success": success
        }

    elif tool_name == "diff_versions":
        from ..core.differ import DiffGenerator

        diff = version_manager.diff_snapshots(
            from_ref=parameters["from_ref"],
            to_ref=parameters.get("to_ref", "current"),
            file_filters=parameters.get("file_filters")
        )

        differ = DiffGenerator(config.diff_format, version_manager.store)
        diff_output = differ.generate_diff(
            diff,
            format=parameters.get("format", "unified")
        )

        filter_note = ""
        if parameters.get("file_filters"):
            filter_note = f"\n🔍 Filtered: {', '.join(parameters['file_filters'])}\n"

        text = f"""📊 Diff between {parameters['from_ref']} and {parameters.get('to_ref', 'current')}
{filter_note}
📈 Changes: {diff.total_changes}
📊 Significance: {diff.significance_score:.1%}

{diff_output}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "diff": diff_output,
            "total_changes": diff.total_changes,
            "significance_score": diff.significance_score
        }

    # ═══════════════════════════════════════════════════════════
    # DOCUMENTATION
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "generate_documentation":
        output_paths = doc_generator.generate(
            output_path=Path(parameters["output_path"]) if parameters.get("output_path") else None,
            include_paths=parameters.get("include_paths"),
            include_tree=parameters.get("include_tree", True),
            include_code=parameters.get("include_code", True),
            split_limit=parameters.get("split_limit"),
            ignore_tree_patterns=parameters.get("ignore_tree_patterns"),
            exclude_paths=parameters.get("ignore_tree_patterns") # Use same patterns for content exclusion
        )

        file_list = "\n".join(f"- {p.name} ({p.stat().st_size / 1024:.1f} KB)" for p in output_paths)

        text = f"""✅ Documentation generated successfully!

📁 Output files:
{file_list}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "output_paths": [str(p) for p in output_paths],
            "files_count": len(output_paths)
        }

    elif tool_name == "preview_structure":
        from ..utils.tree import TreeGenerator
        from ..utils.filters import FileFilter
        import copy

        # Handle ad-hoc filtering
        ignore_config = config.ignore
        if parameters.get("ignore_add"):
            # Create a deep copy to avoid modifying global config
            ignore_config = copy.deepcopy(config.ignore)
            # Add patterns to appropriate lists based on content
            for pattern in parameters["ignore_add"]:
                if pattern.startswith('.'):
                    ignore_config.extensions.append(pattern)
                elif '/' in pattern or '*' in pattern:
                    ignore_config.patterns.append(pattern)
                else:
                    # Ambiguous, add to both files and dirs to be safe
                    ignore_config.files.append(pattern)
                    ignore_config.dirs.append(pattern)

        tree_gen = TreeGenerator()
        file_filter = FileFilter(ignore_config, config.project_path)
        
        # Pagination parameters
        paginate = "page" in parameters or "limit" in parameters
        page = parameters.get("page", 1)
        limit = parameters.get("limit", 50)

        tree = tree_gen.generate(
            config.project_path,
            max_depth=parameters.get("max_depth"),
            filter_func=lambda p: not file_filter.should_ignore(p, p.is_dir()),
            paginate=paginate,
            page=page,
            limit=limit
        )

        text = f"""📁 Project Structure: {config.project_name or config.project_path.name}
{'(Paginated: page ' + str(page) + ' limit ' + str(limit) + ')' if paginate else ''}

{tree}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "tree": tree,
            "page": page if paginate else 1,
            "total_pages": None  # TreeGenerator doesn't calculate total pages easily yet
        }

    elif tool_name == "get_project_stats":
        from ..core.scanner import FileScanner
        from collections import Counter

        scanner = FileScanner(config)
        files = scanner.scan()

        extensions = Counter(Path(f.path).suffix for f in files)
        total_size = sum(f.size for f in files)

        # Format texte
        text_lines = [f"📊 Project Statistics\n"]
        text_lines.append(f"📁 Total files: {len(files)}")
        text_lines.append(f"💾 Total size: {total_size / 1024 / 1024:.2f} MB\n")

        text_lines.append("📈 Top extensions:")
        for ext, count in extensions.most_common(10):
            ext_name = ext if ext else "(no extension)"
            percentage = (count / len(files)) * 100
            text_lines.append(f"  {ext_name}: {count} files ({percentage:.1f}%)")

        return {
            "content": [{"type": "text", "text": "\n".join(text_lines)}],
            "total_files": len(files),
            "total_size": total_size,
            "extensions": dict(extensions.most_common(10))
        }

    # ═══════════════════════════════════════════════════════════
    # CODE INTELLIGENCE
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "get_file_history":
        history = version_manager.get_file_history(parameters["file_path"])

        if not history:
            text = f"📄 No history found for `{parameters['file_path']}`"
        else:
            lines = [f"📄 File History: `{parameters['file_path']}`\n"]
            lines.append(f"📸 Found in {len(history)} snapshot(s)\n")

            for entry in history:
                tag_str = f" ({entry['tag']})" if entry.get('tag') else ""
                status = ""
                if entry.get('removed'):
                    status = "🗑️  REMOVED"
                elif entry.get('first_seen'):
                    status = "✨ FIRST SEEN"
                elif entry.get('changed'):
                    status = "✏️  CHANGED"
                else:
                    status = "━  unchanged"

                size_str = f" ({entry['size']}B)" if entry.get('size') else ""
                lines.append(f"  [{entry['snapshot_id']}]{tag_str} {entry['date'][:10]} {status}{size_str}")
                if entry.get('message'):
                    lines.append(f"      📝 {entry['message']}")

            text = "\n".join(lines)

        return {
            "content": [{"type": "text", "text": text}],
            "history": history
        }

    elif tool_name == "search_snapshots":
        results = version_manager.search_in_snapshots(
            query=parameters["query"],
            file_filter=parameters.get("file_filter"),
            snapshot_ref=parameters.get("snapshot_ref"),
            case_sensitive=parameters.get("case_sensitive", False)
        )

        if not results:
            text = f"🔍 No results for \"{parameters['query']}\""
        else:
            lines = [f"🔍 Search: \"{parameters['query']}\""]
            lines.append(f"📊 {len(results)} file(s) matched\n")

            for r in results:
                tag_str = f" ({r['tag']})" if r.get('tag') else ""
                lines.append(f"📄 [{r['snapshot_id']}]{tag_str} `{r['file_path']}` ({r['total_matches']} matches)")
                for m in r['matches']:
                    lines.append(f"   L{m['line']}: {m['content'][:120]}")
                lines.append("")

            text = "\n".join(lines)

        return {
            "content": [{"type": "text", "text": text}],
            "results": results
        }

    elif tool_name == "generate_changelog":
        changelog = version_manager.generate_changelog(
            from_ref=parameters["from_ref"],
            to_ref=parameters.get("to_ref")
        )

        return {
            "content": [{"type": "text", "text": changelog}],
            "changelog": changelog
        }

    # ═══════════════════════════════════════════════════════════
    # PROJECT MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "init_project":
        from ..core.config import ConfigManager
        # ✅ CORRECTION: Path est déjà importé en haut du fichier

        project_path = Path(parameters["project_path"])
        config_manager = ConfigManager(project_path)

        new_config = config_manager.init_project()

        if parameters.get("preset"):
            config_manager._apply_preset(new_config, parameters["preset"])
            config_manager.save(new_config)

        # Create storage directory
        storage_path = project_path / new_config.storage_path
        storage_path.mkdir(exist_ok=True)

        text = f"""✅ Project initialized!

📁 Project: {project_path}
⚙️  Config: {config_manager.config_path}
💾 Storage: {storage_path}
"""

        if parameters.get("preset"):
            text += f"🎨 Preset: {parameters['preset']}\n"

        return {
            "content": [{"type": "text", "text": text}],
            "config_path": str(config_manager.config_path),
            "storage_path": str(storage_path)
        }

    elif tool_name == "get_project_status":
        from ..storage.database import Database

        db_path = config.project_path / config.storage_path / "gencodedoc.db"

        if not db_path.exists():
            text = """⚠️  No snapshots yet

Run 'init_project' first to initialize the project.
"""
            return {
                "content": [{"type": "text", "text": text}],
                "initialized": False
            }

        db = Database(db_path)
        all_snapshots = db.list_snapshots()
        recent_snapshots = all_snapshots[:5]

        # ✅ NOUVEAU: Vérifier si autosave est vraiment en cours
        autosave_running = False
        if server:
            path_str = str(config.project_path.resolve())
            autosave_running = path_str in server._autosave_managers

        text = f"""📊 Project Status

Project: {config.project_name or config.project_path.name}
Path: {config.project_path}
Total Snapshots: {len(all_snapshots)}
Autosave Config: {'✅ Enabled' if config.autosave.enabled else '❌ Disabled'}
Autosave Running: {'✅ Active' if autosave_running else '❌ Not started'}

Recent Snapshots:
"""

        for snap in recent_snapshots:
            snap_type = "auto" if snap['is_autosave'] else "manual"
            text += f"  [{snap['id']}] {snap['created_at']} - {snap['message'] or '(no message)'} ({snap_type})\n"

        if config.autosave.enabled and not autosave_running:
            text += "\n💡 Tip: Use 'start_autosave' to start automatic versioning.\n"

        return {
            "content": [{"type": "text", "text": text}],
            "initialized": True,
            "project_name": config.project_name or config.project_path.name,
            "total_snapshots": len(all_snapshots),
            "autosave_enabled": config.autosave.enabled,
            "autosave_running": autosave_running
        }

    # ═══════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "get_config":
        import yaml

        config_dict = config.model_dump(exclude={'project_path'}, exclude_none=True, mode='json')

        # Convert Path to string
        if 'storage_path' in config_dict:
            config_dict['storage_path'] = str(config_dict['storage_path'])

        config_yaml = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

        text = f"""⚙️  Project Configuration

{config_yaml}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "config": config_dict
        }

    elif tool_name == "set_config_value":
        from ..core.config import ConfigManager

        key = parameters["key"]
        value = parameters["value"]

        # Parse key path
        keys = key.split('.')

        # Navigate to nested dict
        config_dict = config.model_dump()
        target = config_dict
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value

        # Save
        from ..models.config import ProjectConfig
        updated_config = ProjectConfig(**config_dict)

        config_manager = ConfigManager(config.project_path)
        config_manager.save(updated_config)

        # ✅ NOUVEAU: Invalider le cache pour forcer le rechargement
        if server:
            path_str = str(config.project_path.resolve())
            if path_str in server._managers_cache:
                del server._managers_cache[path_str]

        text = f"""✅ Configuration updated!

{key} = {value}

⚠️  Restart MCP server for changes to take full effect.
"""

        return {
            "content": [{"type": "text", "text": text}],
            "key": key,
            "value": value
        }

    elif tool_name == "apply_preset":
        from ..core.config import ConfigManager

        preset = parameters["preset"]
        config_manager = ConfigManager(config.project_path)

        # ✅ NOUVEAU: Convertir en sets pour éviter doublons
        before_dirs = set(config.ignore.dirs)
        before_files = set(config.ignore.files)
        before_exts = set(config.ignore.extensions)

        config_manager._apply_preset(config, preset)

        # Convertir en lists uniques
        config.ignore.dirs = list(set(config.ignore.dirs))
        config.ignore.files = list(set(config.ignore.files))
        config.ignore.extensions = list(set(config.ignore.extensions))

        config_manager.save(config)

        # ✅ NOUVEAU: Invalider le cache
        if server:
            path_str = str(config.project_path.resolve())
            if path_str in server._managers_cache:
                del server._managers_cache[path_str]

        # Calculer ce qui a été ajouté
        added_dirs = set(config.ignore.dirs) - before_dirs
        added_files = set(config.ignore.files) - before_files
        added_exts = set(config.ignore.extensions) - before_exts

        text = f"""✅ Preset applied: {preset}

Added to ignore:
"""
        if added_dirs:
            text += f"  Directories: {', '.join(added_dirs)}\n"
        if added_files:
            text += f"  Files: {', '.join(added_files)}\n"
        if added_exts:
            text += f"  Extensions: {', '.join(added_exts)}\n"

        if not (added_dirs or added_files or added_exts):
            text += "  (All rules were already present)\n"

        return {
            "content": [{"type": "text", "text": text}],
            "preset": preset,
            "added": {
                "dirs": list(added_dirs),
                "files": list(added_files),
                "extensions": list(added_exts)
            }
        }

    elif tool_name == "manage_ignore_rules":
        from ..core.config import ConfigManager

        if parameters.get("list_all"):
            text = f"""📋 Ignore Rules

Directories: {', '.join(config.ignore.dirs)}
Files: {', '.join(config.ignore.files)}
Extensions: {', '.join(config.ignore.extensions)}
"""
            if config.ignore.patterns:
                text += f"Patterns: {', '.join(config.ignore.patterns)}\n"

            return {
                "content": [{"type": "text", "text": text}],
                "dirs": config.ignore.dirs,
                "files": config.ignore.files,
                "extensions": config.ignore.extensions,
                "patterns": config.ignore.patterns
            }

        modified = False
        changes = []

        # ✅ NOUVEAU: Utiliser des sets pour éviter doublons
        if parameters.get("add_dir"):
            dir_name = parameters["add_dir"]
            if dir_name not in config.ignore.dirs:
                config.ignore.dirs.append(dir_name)
                modified = True
                changes.append(f"Added directory: {dir_name}")
            else:
                changes.append(f"Directory already ignored: {dir_name}")

        if parameters.get("add_file"):
            file_name = parameters["add_file"]
            if file_name not in config.ignore.files:
                config.ignore.files.append(file_name)
                modified = True
                changes.append(f"Added file: {file_name}")
            else:
                changes.append(f"File already ignored: {file_name}")

        if parameters.get("add_ext"):
            ext = parameters["add_ext"]
            if not ext.startswith('.'):
                ext = '.' + ext
            if ext not in config.ignore.extensions:
                config.ignore.extensions.append(ext)
                modified = True
                changes.append(f"Added extension: {ext}")
            else:
                changes.append(f"Extension already ignored: {ext}")

        if modified:
            config_manager = ConfigManager(config.project_path)
            config_manager.save(config)

            # ✅ NOUVEAU: Invalider le cache
            if server:
                path_str = str(config.project_path.resolve())
                if path_str in server._managers_cache:
                    del server._managers_cache[path_str]

            text = "✅ Ignore rules updated!\n\n" + "\n".join(changes)
        else:
            text = "ℹ️  No changes made\n\n" + "\n".join(changes)

        return {
            "content": [{"type": "text", "text": text}],
            "modified": modified,
            "changes": changes
        }

    # ═══════════════════════════════════════════════════════════
    # AUTOSAVE
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "start_autosave":
        if not server:
            return {
                "content": [{"type": "text", "text": "❌ Autosave not supported in this server mode"}],
                "error": "Server reference not available"
            }

        project_path = Path(parameters["project_path"])
        mode = parameters.get("mode", "hybrid")

        result = server.start_autosave(project_path, mode)

        text = f"""✅ Autosave started!

📁 Project: {result['project']}
🔄 Mode: {result['mode']}
📊 Status: {result['status']}
"""

        return {
            "content": [{"type": "text", "text": text}],
            **result
        }

    elif tool_name == "stop_autosave":
        if not server:
            return {
                "content": [{"type": "text", "text": "❌ Autosave not supported in this server mode"}],
                "error": "Server reference not available"
            }

        project_path = Path(parameters["project_path"])

        result = server.stop_autosave(project_path)

        text = f"""✅ Autosave stopped!

📁 Project: {project_path}
📊 Status: {result['status']}
"""

        return {
            "content": [{"type": "text", "text": text}],
            **result
        }

    elif tool_name == "get_autosave_status":
        if not server:
            return {
                "content": [{"type": "text", "text": "❌ Autosave not supported in this server mode"}],
                "error": "Server reference not available"
            }

        status_list = server.get_autosave_status()

        if not status_list:
            text = "ℹ️  No autosave processes running"
        else:
            text = f"🔄 Autosave Status ({len(status_list)} active)\n\n"
            for item in status_list:
                text += f"📁 {item['project']}\n"
                text += f"  Status: {item['status']}\n"
                if item.get('last_save'):
                    text += f"  Last save: {item['last_save']}\n"
                text += "\n"

        return {
            "content": [{"type": "text", "text": text}],
            "active_count": len(status_list),
            "projects": status_list
        }

    # ═══════════════════════════════════════════════════════════
    # FILE EXPLORATION & EXPORT (v2.1.0)
    # ═══════════════════════════════════════════════════════════

    elif tool_name == "get_file_at_version":
        try:
            content = version_manager.get_file_content_at_version(
                snapshot_ref=parameters["snapshot_ref"],
                file_path=parameters["file_path"]
            )

            if content is None:
                text = f"❌ Could not retrieve content for '{parameters['file_path']}'"
                return {"content": [{"type": "text", "text": text}], "error": "content_not_found"}

            text = f"""📄 {parameters['file_path']} @ snapshot {parameters['snapshot_ref']}
{'─' * 60}
{content}
"""
            return {
                "content": [{"type": "text", "text": text}],
                "file_path": parameters["file_path"],
                "snapshot_ref": parameters["snapshot_ref"],
                "size": len(content)
            }
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"❌ {str(e)}"}], "error": str(e)}

    elif tool_name == "list_files_at_version":
        try:
            files = version_manager.list_files_at_version(
                snapshot_ref=parameters["snapshot_ref"],
                pattern=parameters.get("pattern")
            )

            text_lines = [f"📂 Files in snapshot {parameters['snapshot_ref']}"]
            if parameters.get("pattern"):
                text_lines.append(f"🔍 Filter: {parameters['pattern']}")
            text_lines.append(f"📁 Total: {len(files)} files\n")

            for f in files:
                size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] >= 1024 else f"{f['size']} B"
                text_lines.append(f"  {f['path']}  ({size_str})")

            return {
                "content": [{"type": "text", "text": "\n".join(text_lines)}],
                "files": files,
                "count": len(files)
            }
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"❌ {str(e)}"}], "error": str(e)}

    elif tool_name == "restore_files":
        try:
            result = version_manager.restore_snapshot(
                snapshot_ref=parameters["snapshot_ref"],
                force=parameters.get("force", True),
                file_filters=parameters["file_filters"]
            )

            text = f"""✅ Partial restore complete!

📸 Snapshot: {parameters['snapshot_ref']}
🔍 Filters: {', '.join(parameters['file_filters'])}
📁 Restored: {result['restored_count']}/{result['total_files']} files
"""
            if result['files_restored']:
                text += "\nRestored files:\n"
                for f in result['files_restored']:
                    text += f"  ✅ {f}\n"

            if result['files_skipped']:
                text += "\nSkipped files:\n"
                for f in result['files_skipped']:
                    text += f"  ⏭️  {f}\n"

            return {
                "content": [{"type": "text", "text": text}],
                "success": True,
                **result
            }
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"❌ {str(e)}"}], "error": str(e)}

    elif tool_name == "export_snapshot":
        try:
            result = version_manager.export_snapshot(
                snapshot_ref=parameters["snapshot_ref"],
                output_path=Path(parameters["output_path"]),
                archive=parameters.get("archive", False),
                file_filters=parameters.get("file_filters")
            )

            text = f"""✅ Snapshot exported!

📸 Snapshot: {result['snapshot']}
📦 Format: {result['format']}
📂 Output: {result['output_path']}
📁 Files: {result['exported_count']} exported
"""
            if result.get('archive_size'):
                text += f"💾 Archive size: {result['archive_size'] / 1024:.1f} KB\n"

            if result['failed_count'] > 0:
                text += f"\n⚠️  {result['failed_count']} files failed to export\n"

            return {
                "content": [{"type": "text", "text": text}],
                **result
            }
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"❌ {str(e)}"}], "error": str(e)}

    elif tool_name == "cleanup_orphaned_contents":
        count = version_manager.cleanup_orphaned_contents()

        text = f"""🧹 Cleanup complete!

🗑️  Removed {count} orphaned content(s) from the database.
"""
        return {
            "content": [{"type": "text", "text": text}],
            "removed_count": count
        }

    else:
        raise ValueError(f"Unknown tool: {tool_name}")

```

### 📄 `gencodedoc/models/__init__.py`

```python
"""Data models for gencodedoc"""
from .config import ProjectConfig, IgnoreConfig, AutosaveConfig
from .snapshot import Snapshot, SnapshotMetadata, FileEntry, SnapshotDiff

__all__ = [
    "ProjectConfig",
    "IgnoreConfig",
    "AutosaveConfig",
    "Snapshot",
    "SnapshotMetadata",
    "FileEntry",
    "SnapshotDiff",
]

```

### 📄 `gencodedoc/models/config.py`

```python
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

```

### 📄 `gencodedoc/models/snapshot.py`

```python
"""Snapshot data models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import fnmatch

class FileEntry(BaseModel):
    """Single file in a snapshot"""
    path: str
    hash: str
    size: int
    mode: int = 0o644

class SnapshotMetadata(BaseModel):
    """Snapshot metadata"""
    id: Optional[int] = None
    hash: str = ""
    message: Optional[str] = None
    tag: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    parent_id: Optional[int] = None
    is_autosave: bool = False
    trigger_type: str = 'manual'
    files_count: int = 0
    total_size: int = 0
    compressed_size: int = 0

class Snapshot(BaseModel):
    """Complete snapshot"""
    metadata: SnapshotMetadata
    files: List[FileEntry] = Field(default_factory=list)

    def get_file(self, path: str) -> Optional[FileEntry]:
        """Get a specific file entry by path"""
        for f in self.files:
            if f.path == path:
                return f
        return None

    def get_files_matching(self, patterns: List[str]) -> List[FileEntry]:
        """Get files matching glob patterns or path prefixes"""
        matched = []
        for f in self.files:
            for pattern in patterns:
                if fnmatch.fnmatch(f.path, pattern) or f.path.startswith(pattern):
                    matched.append(f)
                    break
        return matched

class DiffEntry(BaseModel):
    """Single file diff"""
    file_path: str
    status: str  # added, removed, modified, renamed
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    diff_content: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0

class SnapshotDiff(BaseModel):
    """Diff between snapshots"""
    from_snapshot: int = 0
    to_snapshot: int = 0
    files_added: List[str] = Field(default_factory=list)
    files_removed: List[str] = Field(default_factory=list)
    files_modified: List[DiffEntry] = Field(default_factory=list)
    files_renamed: List[Dict[str, str]] = Field(default_factory=list)
    total_changes: int = 0
    significance_score: float = 0.0

    def filter_by_paths(self, paths: List[str]) -> 'SnapshotDiff':
        """Return a new SnapshotDiff filtered to only include specified paths"""
        def matches(file_path: str) -> bool:
            for pattern in paths:
                if fnmatch.fnmatch(file_path, pattern):
                    return True
                if file_path.startswith(pattern):
                    return True
                if file_path == pattern:
                    return True
            return False

        filtered = SnapshotDiff(
            from_snapshot=self.from_snapshot,
            to_snapshot=self.to_snapshot,
            files_added=[p for p in self.files_added if matches(p)],
            files_removed=[p for p in self.files_removed if matches(p)],
            files_modified=[e for e in self.files_modified if matches(e.file_path)],
            files_renamed=[r for r in self.files_renamed if matches(r.get('from', '')) or matches(r.get('to', ''))],
        )
        filtered.total_changes = (
            len(filtered.files_added) +
            len(filtered.files_removed) +
            len(filtered.files_modified)
        )
        total = max(self.total_changes, 1)
        filtered.significance_score = filtered.total_changes / total
        return filtered


```

### 📄 `gencodedoc/storage/__init__.py`

```python
"""Storage layer for snapshots and metadata"""
from .database import Database
from .snapshot_store import SnapshotStore
from .compression import Compressor

__all__ = ["Database", "SnapshotStore", "Compressor"]

```

### 📄 `gencodedoc/storage/compression.py`

```python
"""Compression utilities using zstandard"""
import zstandard as zstd
from typing import Tuple

class Compressor:
    """File content compression"""

    def __init__(self, level: int = 3):
        """
        Initialize compressor

        Args:
            level: Compression level (1-22, default 3)
        """
        self.level = max(1, min(22, level))
        self._compressor = zstd.ZstdCompressor(level=self.level)
        self._decompressor = zstd.ZstdDecompressor()

    def compress(self, data: bytes) -> Tuple[bytes, int, int]:
        """
        Compress data

        Returns:
            (compressed_data, original_size, compressed_size)
        """
        original_size = len(data)
        compressed = self._compressor.compress(data)
        compressed_size = len(compressed)

        return compressed, original_size, compressed_size

    def decompress(self, data: bytes) -> bytes:
        """Decompress data, fallback to original if not compressed"""
        try:
            return self._decompressor.decompress(data)
        except zstd.ZstdError:
            # Not compressed or invalid zstd data, return as is
            return data


    def compress_file(self, file_path: str) -> Tuple[bytes, int, int]:
        """
        Compress file content

        Returns:
            (compressed_data, original_size, compressed_size)
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.compress(data)

```

### 📄 `gencodedoc/storage/database.py`

```python
"""SQLite database management"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

class Database:
    """SQLite database for metadata"""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connection(self):
        """Context manager for connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema"""
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    message TEXT,
                    tag TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parent_id INTEGER,
                    is_autosave BOOLEAN DEFAULT 0,
                    trigger_type TEXT,
                    files_count INTEGER,
                    total_size INTEGER,
                    compressed_size INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES snapshots(id)
                );

                CREATE TABLE IF NOT EXISTS snapshot_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    size INTEGER,
                    mode INTEGER,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id),
                    UNIQUE(snapshot_id, file_path)
                );

                CREATE TABLE IF NOT EXISTS file_contents (
                    hash TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    original_size INTEGER,
                    compressed_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS autosave_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_check TIMESTAMP,
                    last_save TIMESTAMP,
                    last_snapshot_id INTEGER,
                    files_tracked INTEGER,
                    FOREIGN KEY (last_snapshot_id) REFERENCES snapshots(id)
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_created ON snapshots(created_at);
                CREATE INDEX IF NOT EXISTS idx_snapshots_tag ON snapshots(tag);
                CREATE INDEX IF NOT EXISTS idx_snapshot_files_hash ON snapshot_files(file_hash);
                CREATE INDEX IF NOT EXISTS idx_file_contents_hash ON file_contents(hash);
            """)

    # Snapshot CRUD
    def create_snapshot(
        self,
        hash: str,
        message: Optional[str] = None,
        tag: Optional[str] = None,
        is_autosave: bool = False,
        trigger_type: str = 'manual',
        parent_id: Optional[int] = None,
        files_count: int = 0,
        total_size: int = 0,
        compressed_size: int = 0
    ) -> int:
        """Create new snapshot record"""
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO snapshots
                (hash, message, tag, is_autosave, trigger_type, parent_id,
                 files_count, total_size, compressed_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (hash, message, tag, is_autosave, trigger_type, parent_id,
                  files_count, total_size, compressed_size))
            return cursor.lastrowid

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_snapshot_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """Get snapshot by tag"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM snapshots WHERE tag = ?",
                (tag,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_snapshots(
        self,
        limit: Optional[int] = None,
        include_autosave: bool = True
    ) -> List[Dict[str, Any]]:
        """List snapshots"""
        with self.connection() as conn:
            query = "SELECT * FROM snapshots"
            params = []

            if not include_autosave:
                query += " WHERE is_autosave = 0"

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get most recent snapshot"""
        snapshots = self.list_snapshots(limit=1)
        return snapshots[0] if snapshots else None

    def delete_snapshot(self, snapshot_id: int) -> None:
        """Delete snapshot and its files"""
        with self.connection() as conn:
            conn.execute("DELETE FROM snapshot_files WHERE snapshot_id = ?", (snapshot_id,))
            conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))

    # Snapshot files
    def add_file_to_snapshot(
        self,
        snapshot_id: int,
        file_path: str,
        file_hash: str,
        size: int,
        mode: int
    ) -> None:
        """Add file to snapshot"""
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO snapshot_files (snapshot_id, file_path, file_hash, size, mode)
                VALUES (?, ?, ?, ?, ?)
            """, (snapshot_id, file_path, file_hash, size, mode))

    def get_snapshot_files(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Get all files in snapshot"""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM snapshot_files WHERE snapshot_id = ?
            """, (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]

    # File contents (with deduplication)
    def store_content(
        self,
        content_hash: str,
        content: bytes,
        original_size: int,
        compressed_size: int
    ) -> None:
        """Store file content (deduplicated)"""
        with self.connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO file_contents
                (hash, content, original_size, compressed_size)
                VALUES (?, ?, ?, ?)
            """, (content_hash, content, original_size, compressed_size))

    def get_content(self, content_hash: str) -> Optional[bytes]:
        """Get file content by hash"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT content FROM file_contents WHERE hash = ?",
                (content_hash,)
            )
            row = cursor.fetchone()
            return row['content'] if row else None

    def content_exists(self, content_hash: str) -> bool:
        """Check if content exists"""
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM file_contents WHERE hash = ? LIMIT 1",
                (content_hash,)
            )
            return cursor.fetchone() is not None

    # Autosave state
    def update_autosave_state(
        self,
        last_check: Optional[datetime] = None,
        last_save: Optional[datetime] = None,
        last_snapshot_id: Optional[int] = None,
        files_tracked: Optional[int] = None
    ) -> None:
        """Update autosave state"""
        with self.connection() as conn:
            # Ensure row exists
            conn.execute("""
                INSERT OR IGNORE INTO autosave_state (id) VALUES (1)
            """)

            updates = []
            params = []

            if last_check:
                updates.append("last_check = ?")
                params.append(last_check)
            if last_save:
                updates.append("last_save = ?")
                params.append(last_save)
            if last_snapshot_id:
                updates.append("last_snapshot_id = ?")
                params.append(last_snapshot_id)
            if files_tracked is not None:
                updates.append("files_tracked = ?")
                params.append(files_tracked)

            if updates:
                params.append(1)
                conn.execute(
                    f"UPDATE autosave_state SET {', '.join(updates)} WHERE id = ?",
                    params
                )

    def get_autosave_state(self) -> Optional[Dict[str, Any]]:
        """Get autosave state"""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM autosave_state WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    # Cleanup
    def cleanup_old_autosaves(self, max_keep: int = 50) -> int:
        """Delete old autosaves beyond retention limit"""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT id FROM snapshots
                WHERE is_autosave = 1
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            """, (max_keep,))

            old_ids = [row['id'] for row in cursor.fetchall()]

            for snapshot_id in old_ids:
                self.delete_snapshot(snapshot_id)

            return len(old_ids)

    def cleanup_expired_autosaves(self, delete_after_days: int) -> int:
        """Delete autosaves older than X days"""
        if delete_after_days <= 0:
            return 0
            
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT id FROM snapshots
                WHERE is_autosave = 1
                AND created_at < datetime('now', ?)
            """, (f'-{delete_after_days} days',))

            old_ids = [row['id'] for row in cursor.fetchall()]

            for snapshot_id in old_ids:
                self.delete_snapshot(snapshot_id)

            return len(old_ids)

    def cleanup_orphaned_contents(self) -> int:
        """Remove file_contents that are no longer referenced by any snapshot"""
        with self.connection() as conn:
            cursor = conn.execute("""
                DELETE FROM file_contents
                WHERE hash NOT IN (
                    SELECT DISTINCT file_hash FROM snapshot_files
                )
            """)
            return cursor.rowcount

```



---
**🚀 Suite dans la partie suivante...**