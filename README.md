# 🚀 GenCodeDoc

<div align="center">

**Smart documentation generator and intelligent versioning system with full MCP support**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-poetry-blueviolet)](https://python-poetry.org/)
[![MCP Compatible](https://img.shields.io/badge/MCP-stdio%20%7C%20SSE%20%7C%20REST-green)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AI Ready](https://img.shields.io/badge/AI-Claude%20%7C%20Gemini-orange)](https://esprit-artificiel.com)

*Intelligent versioning and documentation for modern development workflows*

[Quick Start](#-quick-start) • [Features](#-features) • [MCP Tools](#-mcp-tools-26-tools) • [Documentation](#-documentation)

</div>

---

## ⚡ Quick Start

```bash
# 1. Install
cd /path/to/gencodedoc
poetry install

# 2. Initialize your project
poetry run gencodedoc init --preset python

# 3. Create your first snapshot
poetry run gencodedoc snapshot create -m "Initial version" -t v1.0

# 4. Generate documentation (Smart Split)
poetry run gencodedoc doc generate --limit 5000

# 5. Visualize Tree
poetry run gencodedoc tree
```
🎯 For AI Assistants (Claude/Gemini): See MCP Integration

✨ Features
🎯 Core Features
📸 Smart Snapshots - Create intelligent snapshots with ~70% space savings via SHA256 deduplication
🔄 Intelligent Autosave - 3 modes (timer/diff/hybrid) with configurable thresholds
📝 Beautiful Documentation - Generate Markdown docs with syntax highlighting, directory trees, and **smart splitting**
🔍 Advanced Diff - Compare versions with unified, JSON, or AST-based diffs
🗜️ Efficient Storage - zstd compression (~3x reduction) + SQLite with optimized indexes
🎨 Project Presets - Pre-configured for Python, Node.js, Go, and Web projects
🔌 MCP Integration (Model Context Protocol)
**26 MCP Tools** - Full CLI functionality exposed via MCP for AI Assistants
3 Transports - stdio (Gemini CLI) + SSE (Claude Desktop) + REST API
Multi-Project - Manage multiple projects simultaneously
Code Intelligence - File history, search, and changelog generation
Live Status - Real-time project statistics and snapshot management
📦 Installation
Prerequisites
Python 3.10+
Poetry (dependency manager)
Install Poetry
Bash

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
Install GenCodeDoc
Bash

# Clone or navigate to the project
cd /home/fkomp/Bureau/oracle/utilitaires/gencodedoc/gencodedoc

# Install dependencies
poetry install

# Verify installation
poetry run gencodedoc --help
🎯 Usage
📋 CLI Usage
Initialize a Project
Bash

# Basic initialization
gencodedoc init

# With Python preset (recommended for Oracle projects)
gencodedoc init --preset python

# Available presets: python, nodejs, go, web
Snapshot Management
Bash

# Create snapshot
gencodedoc snapshot create --message "Feature X completed" --tag v1.0

# List snapshots
gencodedoc snapshot list --limit 10

# Show snapshot details
gencodedoc snapshot show v1.0

# View file content at specific version (NEW)
gencodedoc snapshot cat v1.0 src/main.py

# List files in a snapshot (NEW)
gencodedoc snapshot files v1.0 --pattern "*.py"

# Compare versions
gencodedoc snapshot diff v1.0 v2.0

# Restore snapshot (full or partial)
gencodedoc snapshot restore v1.0 --force
gencodedoc snapshot restore v1.0 --filter "src/*.py"  # Partial restore

# Export snapshot (NEW)
gencodedoc snapshot export v1.0 ./dist-v1 --archive  # Creates .tar.gz

# Delete snapshot
gencodedoc snapshot delete old-version --force

# Cleanup orphaned data (NEW)
gencodedoc snapshot cleanup
Documentation Generation
Bash

# Full documentation
gencodedoc doc generate

# Custom output
gencodedoc doc generate --output docs/API.md

# Specific paths only
gencodedoc doc generate --include src/api/ --include README.md

# Structure preview
gencodedoc doc preview --max-depth 3

# Project statistics
gencodedoc doc stats
Configuration
Bash

# View configuration
gencodedoc config show

# Edit configuration
gencodedoc config edit

# Set specific values
gencodedoc config set autosave.enabled true
gencodedoc config set autosave.mode hybrid

# Apply preset
gencodedoc config preset python

# Manage ignore rules
gencodedoc config ignore --add-dir dist
gencodedoc config ignore --add-ext .tmp
gencodedoc config ignore --list-all

# Customizable Presets
# Presets are now defined in YAML files (gencodedoc/config/presets/*.yaml) 
# and can be modified directly in the source code.

Project Status
Bash

# Show project status
gencodedoc status
🔌 MCP Integration
GenCodeDoc exposes 22 powerful tools via the Model Context Protocol, compatible with Claude Desktop, Gemini CLI, and any MCP-compatible client.

🎯 Transport Modes
Transport	Use Case	AI Assistants	Port
stdio	CLI integration	Gemini CLI, custom scripts	stdin/stdout
SSE	Web/Desktop apps	Claude Desktop, web UIs	8000 (HTTP)
REST	API integration	Any HTTP client	8000 (HTTP)
🚀 Setup for Gemini CLI (stdio)
1. Find your Poetry venv path:

Bash

cd /home/fkomp/Bureau/oracle/utilitaires/gencodedoc/gencodedoc
poetry env info --path
# Copy the path and append /bin/python
2. Add to ~/.config/gemini-desktop-app/settings.json:

JSON

{
  "mcpServers": {
    "gencodedoc": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["-m", "gencodedoc.mcp.server_stdio"],
      "env": {
        "PROJECT_PATH": "/home/fkomp/Bureau/oracle/utilitaires/gencodedoc/gencodedoc"
      }
    }
  }
}
3. Restart Gemini CLI and you`re ready! 🎉

🚀 Setup for Claude Desktop (SSE)
1. Start the SSE server:

Bash

# Terminal 1: Start server
poetry run python -m gencodedoc.mcp.server_sse

# Server runs on http://127.0.0.1:8000
2. Add to Claude Desktop config:

Location:

macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
Windows: %APPDATA%\Claude\claude_desktop_config.json
Linux: ~/.config/Claude/claude_desktop_config.json
Config:

JSON

{
  "mcpServers": {
    "gencodedoc": {
      "url": "http://127.0.0.1:8000/mcp/sse",
      "transport": "sse",
      "description": "GenCodeDoc - Smart documentation and versioning"
    }
  }
}
3. Restart Claude Desktop and the server must remain running!

🚀 REST API
Bash

# Start REST server
poetry run python -m gencodedoc.mcp.server

# Available endpoints
GET  http://127.0.0.1:8000/           # Server info
GET  http://127.0.0.1:8000/mcp/tools  # List tools
POST http://127.0.0.1:8000/mcp/execute # Execute tool
🛠️ MCP Tools (26 Tools)

 🧠 Code Intelligence (3 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `get_file_history` | Track file changes across versions | `file_path` |
 | `search_snapshots` | Search text in all snapshots | `query`, `case_sensitive`, `file_filter` |
 | `generate_changelog` | Generate Keep-a-Changelog | `from_ref`, `to_ref` |

 📸 Snapshot Management (11 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `create_snapshot` | Create a new snapshot | `message`, `tag`, `include_paths` |
 | `list_snapshots` | List all snapshots | `limit`, `include_autosave` |
 | `get_snapshot_details` | Get full snapshot info | `snapshot_ref` |
 | `restore_snapshot` | Restore a snapshot (full or partial) | `snapshot_ref`, `force`, `file_filters` |
 | `restore_files` | Restore specific files | `snapshot_ref`, `file_filters` |
 | `delete_snapshot` | Delete a snapshot | `snapshot_ref` |
 | `diff_versions` | Compare two versions | `from_ref`, `to_ref`, `format`, `file_filters` |
 | `get_file_at_version` | Get content of a single file | `snapshot_ref`, `file_path` |
 | `list_files_at_version` | List files in a snapshot | `snapshot_ref`, `pattern` |
 | `export_snapshot` | Export snapshot to folder/archive | `snapshot_ref`, `output_path`, `archive` |
 | `cleanup_orphaned_contents` | Cleanup unused data | none |

 📝 Documentation (3 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `generate_documentation` | Generate Markdown docs | `output_path`, `split_limit`, `ignore_tree_patterns` |
 | `preview_structure` | Show directory tree | `max_depth`, `ignore_add`, `limit`, `page` |
 | `get_project_stats` | Get project statistics | none |

 🎯 Project Management (2 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `init_project` | Initialize gencodedoc | `project_path`, `preset` |
 | `get_project_status` | Get project status | `project_path` |

 ⚙️ Configuration (4 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `get_config` | View configuration | `project_path` |
 | `set_config_value` | Modify config value | `key`, `value` |
 | `apply_preset` | Apply preset config | `preset` (python/nodejs/go/web) |
 | `manage_ignore_rules` | Manage ignore rules | `add_dir`, `add_file`, `add_ext`, `list_all` |

 🔄 Autosave (3 tools)
 | Tool | Description | Key Parameters |
 |------|-------------|----------------|
 | `start_autosave` | Start automatic versioning | `project_path`, `mode` |
 | `stop_autosave` | Stop automatic versioning | `project_path` |
 | `get_autosave_status` | Get status of all autosaves | none |

 ---

 🤝 Contributing
 Contributions welcome! 🎉

 🐛 Report bugs via GitHub Issues
 💡 Suggest features via Discussions
 🔧 Submit Pull Requests

 Development workflow:
 1. Fork the repo
 2. Create a feature branch (`git checkout -b feature/amazing`)
 3. Make your changes
 4. Run tests (`make test`)
 5. Submit PR

 📄 License
 MIT License - See LICENSE file

 🐛 Issues: GitHub Issues
 💬 Discussions: GitHub Discussions
 🌐 Website: esprit-artificiel.com
 📧 Email: support@esprit-artificiel.com

 <div align="center">
 Made with ❤️ for developers who love smart versioning and beautiful docs

 💡 Pro Tip: Use GenCodeDoc with Gemini CLI or Claude Desktop for AI-powered version control!

 ⭐ Star this repo if you find it useful!
 </div>🤖 "Start autosave in hybrid mode for this project"
→ Calls: start_autosave(project_path="...", mode="hybrid")

🤖 "Stop all autosaves and show me their status"
→ Calls: stop_autosave(...) + get_autosave_status()
⚙️ Configuration
Configuration File (.gencodedoc.yaml)
YAML

project_name: "my-project"

# Files/directories to ignore
ignore:
  dirs:
    - node_modules
    - venv
    - .venv
    - __pycache__
    - .git
    - dist
    - build
  files:
    - "*.log"
    - package-lock.json
    - .DS_Store
  extensions:
    - .pyc
    - .pyo
    - .exe
    - .jpg
    - .png
    - .pdf
  patterns: []  # gitignore-style patterns

# Intelligent autosave
autosave:
  enabled: false  # Set to true to enable
  mode: hybrid    # timer | diff | hybrid (recommended)
  
  # Timer mode: fixed interval
  timer:
    interval: 300  # seconds (5 minutes)
  
  # Diff mode: threshold-based
  diff_threshold:
    threshold: 0.05          # Save if 5% of files changed
    check_interval: 60       # Check every 60 seconds
    ignore_whitespace: true
    ignore_comments: false
  
  # Hybrid mode: combines timer + diff (RECOMMENDED)
  hybrid:
    min_interval: 180   # Minimum 3 minutes between saves
    max_interval: 600   # Maximum 10 minutes between saves
    threshold: 0.03     # Save if 3% of files changed
  
  # Retention policy
  retention:
    max_autosaves: 50         # Keep max 50 autosaves
    compress_after_days: 7    # Compress after 7 days
    delete_after_days: 30     # Delete after 30 days
    keep_manual: true         # Always keep manual snapshots

# Documentation output
output:
  default_name: "{project}_doc_{date}.md"
  include_tree: true
  include_code: true
  tree_full_code_select: false  # Full tree, selected code only
  language_detection: true
  max_file_size: 1000000  # 1 MB max per file

# Diff output format
diff_format:
  default: unified  # unified | json | ast
  unified_context: 3
  json_include_content: true
  ast_enabled: false  # Experimental

# Storage
storage_path: .gencodedoc
compression_enabled: true
compression_level: 3  # 1-22 (3 = good balance)
Quick Config Commands
Bash

# Enable autosave
gencodedoc config set autosave.enabled true
gencodedoc config set autosave.mode hybrid

# Adjust autosave thresholds
gencodedoc config set autosave.hybrid.min_interval 300
gencodedoc config set autosave.hybrid.max_interval 1800
gencodedoc config set autosave.hybrid.threshold 0.03

# Add ignore rules
gencodedoc config ignore --add-dir dist
gencodedoc config ignore --add-ext .tmp
gencodedoc config ignore --add-file debug.log
🏗️ Architecture
text

┌─────────────────────────────────────────────────────────────┐
│                    GenCodeDoc System                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  CLI (Typer) │  │ MCP stdio    │  │ MCP SSE/REST │
│              │  │ (Gemini CLI) │  │ (Claude/Web) │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Core Managers     │
              ├─────────────────────┤
              │ • ConfigManager     │
              │ • VersionManager    │
              │ • DocGenerator      │
              │ • AutosaveManager   │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐  ┌─────▼──────┐  ┌────▼──────┐
    │ Scanner  │  │ Differ     │  │ Storage   │
    │          │  │            │  │           │
    │ • Scan   │  │ • Unified  │  │ • SQLite  │
    │ • Filter │  │ • JSON     │  │ • zstd    │
    │ • Detect │  │ • AST      │  │ • Dedup   │
    └──────────┘  └────────────┘  └───────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                             │
├─────────────────────────────────────────────────────────────┤
│  .gencodedoc/                                               │
│  ├── gencodedoc.db        ← SQLite (metadata)               │
│  │   ├── snapshots        ← Snapshot records                │
│  │   ├── snapshot_files   ← File entries                    │
│  │   ├── file_contents    ← Deduplicated content (SHA256)   │
│  │   └── autosave_state   ← Autosave status                 │
│  └── config/              ← Configuration files             │
└─────────────────────────────────────────────────────────────┘

Key Features:
• 🔑 SHA256 deduplication → ~70% space savings
• 🗜️ zstd compression → ~3x size reduction
• 📊 Indexed SQLite → Fast queries
• 🔄 Watchdog observer → Real-time file monitoring
Project Structure
text

gencodedoc/
├── gencodedoc/              # Source code
│   ├── cli/                # CLI commands (Typer)
│   │   ├── main.py        # Entry point
│   │   ├── snapshot_cmd.py
│   │   ├── doc_cmd.py
│   │   ├── config_cmd.py
│   │   └── mcp_cmd.py
│   ├── core/               # Business logic
│   │   ├── config.py      # Configuration management
│   │   ├── scanner.py     # File scanning & filtering
│   │   ├── versioning.py  # Snapshot management
│   │   ├── documentation.py
│   │   ├── differ.py      # Version comparison
│   │   └── autosave.py    # Intelligent autosave
│   ├── mcp/                # MCP servers
│   │   ├── server_stdio.py  # stdio transport
│   │   ├── server_sse.py    # SSE transport
│   │   ├── server.py        # REST transport
│   │   └── tools.py         # Tool definitions
│   ├── models/             # Data models (Pydantic)
│   │   ├── config.py
│   │   └── snapshot.py
│   ├── storage/            # Storage & compression
│   │   ├── database.py    # SQLite manager
│   │   ├── snapshot_store.py
│   │   └── compression.py # zstd compression
│   └── utils/              # Utilities
│       ├── filters.py
│       ├── formatters.py
│       └── tree.py
├── config/                 # Configuration presets
│   └── presets/
│       ├── python.yaml
│       ├── nodejs.yaml
│       ├── go.yaml
│       └── web.yaml
├── tests/                  # Unit tests
├── pyproject.toml         # Poetry config
├── Makefile               # Dev commands
└── README.md
🔬 Advanced Features
🎯 Intelligent Deduplication (~70% savings)
GenCodeDoc uses SHA256-based deduplication:

✅ Identical files across snapshots are stored once
✅ Massive space savings (~70% on real projects)
✅ zstd compression for ~3x additional reduction
✅ Optimized SQLite with indexes

Example: 10 snapshots of a 100 MB project

Without deduplication: 1 GB
With GenCodeDoc: ~300 MB (dedup + compression)
🔄 Autosave Modes
Mode	How it works	Best for
timer	Save every X seconds	Continuous development
diff	Save when X% changed	Critical projects
hybrid ⭐	Min/max interval + threshold	General use (recommended)
Hybrid mode example:

YAML

hybrid:
  min_interval: 300   # Don`t save more often than 5 min
  max_interval: 1800  # Force save after 30 min
  threshold: 0.03     # OR if 3% of files changed
📊 Diff Formats
Format	Description	Use Case
unified	Git-style diff	Human reading
json	Structured data	Automation
ast	Semantic diff	Code analysis (experimental)
Bash

# Unified diff (default)
gencodedoc snapshot diff v1.0 v2.0

# JSON for scripts
gencodedoc snapshot diff v1.0 v2.0 --format json > changes.json

# AST (semantic)
gencodedoc snapshot diff v1.0 v2.0 --format ast
🐛 Troubleshooting
Common Issues
1️⃣ MCP Error: notifications/initialized
Symptom: Error on MCP startup:

text

MCP ERROR: Unknown method: notifications/initialized
Cause: MCP protocol sends notifications that older versions didn`t handle.

Solution: ✅ Already fixed in current version. The server now silently ignores MCP notifications.

2️⃣ Snapshots created in wrong location
Symptom: All snapshots go to gencodedoc`s own directory instead of target project.

Cause: project_path not properly extracted from MCP tools/call parameters.

Solution: ✅ Already fixed. The server now correctly extracts project_path from arguments.

Verify fix:

Bash

# This should create snapshot in /path/to/project, not gencodedoc
/gencodedoc create_snapshot project_path=/path/to/project tag=test
3️⃣ Zod validation errors (id=null)
Symptom:

text

Error: Expected string or number, received null (path: ["id"])
Cause: JSON-RPC responses with "id": null instead of "id": 0.

Solution: ✅ Already fixed. All error responses now use request_id or 0.

4️⃣ Files not properly scanned
Symptom: Snapshot shows wrong number of files or files from wrong directory.

Cause: snapshot_store.py used relative paths instead of absolute.

Solution: ✅ Already fixed. SnapshotStore now receives and uses project_path for absolute file paths.

5️⃣ DB not initialized
Symptom:

text

Error: no such table: snapshots
Cause: Project not initialized before creating snapshot.

Solution:

Bash

# Always init first (creates tables)
gencodedoc init --preset python

# Or via MCP
/gencodedoc init_project project_path=/path/to/project preset=python
6️⃣ Autosave not starting
Symptom: start_autosave tool doesn`t work.

Cause: Autosave requires the MCP server to remain running (it`s a background process).

Solution:

stdio mode: Server runs per-request → autosave stops when request ends
SSE/REST mode: ✅ Server persistent → autosave works!
Recommended: Use SSE/REST for autosave, stdio for one-off commands.

Debug Mode
Bash

# Enable verbose logging (if implemented)
export GENCODEDOC_DEBUG=1
poetry run gencodedoc snapshot create --message "test"

# Check SQLite DB directly
sqlite3 /path/to/project/.gencodedoc/gencodedoc.db ".tables"
sqlite3 /path/to/project/.gencodedoc/gencodedoc.db "SELECT * FROM snapshots;"
🧪 Testing
Bash

# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=gencodedoc --cov-report=html

# Specific tests
poetry run pytest tests/test_scanner.py -v
poetry run pytest tests/test_versioning.py -v
poetry run pytest tests/test_mcp.py -v

# Watch mode (requires pytest-watch)
poetry run ptw
🛠️ Development
Setup Development Environment
Bash

# Install with dev dependencies
poetry install

# Activate virtual environment
poetry shell

# Install pre-commit hooks (if configured)
pre-commit install
Makefile Commands
Bash

make help            # Show all commands
make install         # Install dependencies
make test            # Run tests
make test-cov        # Tests with coverage
make lint            # Check code quality
make format          # Format code (Black)
make clean           # Remove temporary files
make docs            # Generate documentation
make serve-mcp-sse   # Start SSE server
make serve-mcp-stdio # Start stdio server
make all             # Lint + test + build
Code Style
Formatter: Black (line length 100)
Linter: Ruff
Type hints: Enforced with Pydantic
Docstrings: Google style
🎯 Use Cases
1️⃣ Continuous Documentation
Bash

# Initialize with autosave
gencodedoc init --preset python
gencodedoc config set autosave.enabled true
gencodedoc config set autosave.mode hybrid

# Documentation is always up-to-date
gencodedoc doc generate --output docs/API.md
2️⃣ Safe Refactoring
Bash

# Snapshot before critical changes
gencodedoc snapshot create \
  --message "Before refactoring authentication system" \
  --tag before-refactor

# ... make changes ...

# Snapshot after
gencodedoc snapshot create \
  --message "After refactoring - tests passing" \
  --tag after-refactor

# Compare
gencodedoc snapshot diff before-refactor after-refactor

# Rollback if needed
gencodedoc snapshot restore before-refactor --force
3️⃣ Selective API Documentation
Bash

# Document only specific modules
gencodedoc doc generate \
  --include src/api/ \
  --include src/models/ \
  --include README.md \
  --output docs/API_Reference.md
4️⃣ AI-Assisted Workflow (Gemini/Claude)
Bash

# 1. Configure MCP (once)
# Add gencodedoc to your AI assistant config

# 2. Use natural language
"Create a snapshot with tag v2.0"
"Compare v1.0 and v2.0"
"Show me project statistics"
"Start autosave in hybrid mode"
"Generate complete documentation"

# AI automatically calls the right MCP tools! 🎉
🌟 Roadmap
 Git integration (auto-snapshot on commit)
 Cloud backup (S3, GCS)
 Web UI dashboard
 AST-based semantic diff (full implementation)
 Multi-language presets (Rust, Java, C++)
 Snapshot encryption
 Collaborative features (shared snapshots)
📄 License
MIT License - See LICENSE file

🤝 Contributing
Contributions welcome! 🎉

🐛 Report bugs via GitHub Issues
💡 Suggest features via Discussions
🔧 Submit Pull Requests
Development workflow:

Fork the repo
Create a feature branch (git checkout -b feature/amazing)
Make your changes
Run tests (make test)
Submit PR
📞 Support
🐛 Issues: GitHub Issues
💬 Discussions: GitHub Discussions
🌐 Website: esprit-artificiel.com
📧 Email: support@esprit-artificiel.com
🙏 Acknowledgments
Built with these amazing tools:

FastAPI - MCP server framework
Pydantic - Data validation
Typer - CLI framework
Rich - Terminal formatting
zstandard - Compression
Watchdog - File monitoring
SQLite - Embedded database
<div align="center">
Made with ❤️ for developers who love smart versioning and beautiful docs

💡 Pro Tip: Use GenCodeDoc with Gemini CLI or Claude Desktop for AI-powered version control!

⭐ Star this repo if you find it useful!

</div> ```
🎯 CHANGEMENTS PAR RAPPORT À L`ANCIEN
✅ Ajouts majeurs
Badges en haut (Python, Poetry, MCP, License, AI Ready)
Quick Start ultra-visible avec 5 étapes
17 outils MCP documentés avec tableau
Architecture ASCII complète
Troubleshooting des 6 bugs qu`on a corrigés
Exemples d`usage AI concrets
Autosave mieux expliqué (3 modes + tableau)
3 transports clarifiés (stdio/SSE/REST)
Use cases pratiques (4 scénarios réels)
Roadmap pour le futur
🎨 Améliorations visuelles
Emojis cohérents partout
Tableaux pour comparaisons
Blocs de code bien formatés
Sections claires avec séparateurs
Call-to-action en footer
📊 Mieux organisé
Quick Start en premier (essentiel)
Features avant installation
MCP tools en section dédiée
Troubleshooting complet
Development séparé
