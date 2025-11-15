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
            "description": "Restore a previous snapshot",
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
            "description": "Compare two versions",
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
                        "enum": ["unified", "json"],
                        "description": "Diff output format",
                        "default": "unified"
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
        success = version_manager.restore_snapshot(
            snapshot_ref=parameters["snapshot_ref"],
            force=parameters.get("force", False)
        )

        text = f"""{'✅ Snapshot restored successfully!' if success else '❌ Failed to restore snapshot'}

📸 Snapshot: {parameters['snapshot_ref']}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "success": success
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
            to_ref=parameters.get("to_ref", "current")
        )

        differ = DiffGenerator(config.diff_format, version_manager.store)
        diff_output = differ.generate_diff(
            diff,
            format=parameters.get("format", "unified")
        )

        text = f"""📊 Diff between {parameters['from_ref']} and {parameters.get('to_ref', 'current')}

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
        output_path = doc_generator.generate(
            output_path=Path(parameters["output_path"]) if parameters.get("output_path") else None,
            include_paths=parameters.get("include_paths"),
            include_tree=parameters.get("include_tree", True),
            include_code=parameters.get("include_code", True)
        )

        text = f"""✅ Documentation generated successfully!

📄 Output: {output_path}
💾 Size: {output_path.stat().st_size / 1024:.1f} KB
"""

        return {
            "content": [{"type": "text", "text": text}],
            "output_path": str(output_path)
        }

    elif tool_name == "preview_structure":
        from ..utils.tree import TreeGenerator
        from ..utils.filters import FileFilter

        tree_gen = TreeGenerator()
        file_filter = FileFilter(config.ignore, config.project_path)

        tree = tree_gen.generate(
            config.project_path,
            max_depth=parameters.get("max_depth"),
            filter_func=lambda p: not file_filter.should_ignore(p, p.is_dir())
        )

        text = f"""📁 Project Structure: {config.project_name or config.project_path.name}

{tree}
"""

        return {
            "content": [{"type": "text", "text": text}],
            "tree": tree
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

    else:
        raise ValueError(f"Unknown tool: {tool_name}")
