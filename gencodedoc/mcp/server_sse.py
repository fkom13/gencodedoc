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
