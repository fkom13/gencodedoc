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
