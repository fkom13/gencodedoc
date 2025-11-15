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
