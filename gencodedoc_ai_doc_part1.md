# Documentation du projet: gencodedoc
> Généré le 12/02/2026 04:14:18

## 📂 Structure du projet

```
gencodedoc
├── config
│   └── presets
│       ├── go.yaml
│       ├── nodejs.yaml
│       ├── python.yaml
│       └── web.yaml
├── gencodedoc
│   ├── cli
│   │   ├── __init__.py
│   │   ├── config_cmd.py
│   │   ├── doc_cmd.py
│   │   ├── main.py
│   │   ├── mcp_cmd.py
│   │   ├── snapshot_cmd.py
│   │   └── tree_cmd.py
│   ├── config
│   │   └── presets
│   │       ├── go.yaml
│   │       ├── nodejs.yaml
│   │       ├── python.yaml
│   │       └── web.yaml
│   ├── core
│   │   ├── __init__.py
│   │   ├── autosave.py
│   │   ├── config.py
│   │   ├── differ.py
│   │   ├── documentation.py
│   │   ├── scanner.py
│   │   └── versioning.py
│   ├── mcp
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── server_sse.py
│   │   ├── server_stdio.py
│   │   └── tools.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── snapshot.py
│   ├── storage
│   │   ├── __init__.py
│   │   ├── compression.py
│   │   ├── database.py
│   │   └── snapshot_store.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── filters.py
│   │   ├── formatters.py
│   │   └── tree.py
│   ├── __init__.py
│   └── __main__.py
├── tests
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_documentation.py
│   ├── test_mcp.py
│   ├── test_scanner.py
│   ├── test_storage.py
│   ├── test_utils.py
│   └── test_versioning.py
├── LICENSE
├── Makefile
├── README.md
├── cleanup_sqlite3.sh
├── pyproject.toml
└── rsync_sync.sh```

## 📝 Contenu des fichiers

### 📄 `.gencodedoc.example.yaml`

```yaml
# gencodedoc Configuration Example
# Copy to .gencodedoc.yaml and customize

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
    - .next
    - coverage

  files:
    - .DS_Store
    - "*.log"
    - package-lock.json
    - yarn.lock

  extensions:
    - .pyc
    - .pyo
    - .exe
    - .bin
    - .jpg
    - .png
    - .gif
    - .mp4
    - .pdf
    - .zip

  patterns:
    - "**/*.min.js"
    - "**/*.min.css"
    - "**/temp_*"

# Autosave configuration
autosave:
  enabled: false
  mode: hybrid  # timer | diff | hybrid

  timer:
    interval: 300  # seconds (5 minutes)

  diff_threshold:
    threshold: 0.05  # 5% of files changed
    check_interval: 60  # check every 60 seconds
    ignore_whitespace: true
    ignore_comments: false

  hybrid:
    min_interval: 180  # minimum 3 minutes between saves
    max_interval: 600  # maximum 10 minutes without save
    threshold: 0.03    # 3% change threshold

  retention:
    max_autosaves: 50
    compress_after_days: 7
    delete_after_days: 30
    keep_manual: true  # always keep manual snapshots

# Diff format configuration
diff_format:
  default: unified  # unified | json | ast
  unified_context: 3
  json_include_content: true
  ast_enabled: false  # AST-based semantic diff (heavier)

# Documentation output
output:
  default_name: "{project}_doc_{date}.md"
  include_tree: true
  include_code: true
  tree_full_code_select: false  # full tree but only selected files' code
  language_detection: true
  max_file_size: 1000000  # 1MB

# Storage
storage_path: .gencodedoc
compression_enabled: true
compression_level: 3  # zstd level (1-22)

```

### 📄 `.gencodedoc.yaml`

```yaml
project_name: gencodedoc
ignore:
  dirs:
  - node_modules
  - venv
  - .venv
  - env
  - __pycache__
  - .git
  - dist
  - build
  - .next
  - coverage
  - venv
  - .venv
  - __pycache__
  - venv
  - .venv
  - __pycache__
  - dist
  - build
  files:
  - .DS_Store
  - Thumbs.db
  - package-lock.json
  - yarn.lock
  extensions:
  - .log
  - .pyc
  - .pyo
  - .exe
  - .bin
  - .jpg
  - .png
  - .gif
  - .mp4
  - .pdf
  - .zip
  - .pyc
  - .pyo
  - .pyc
  - .pyo
  - .pyd
  patterns: []
autosave:
  enabled: true
  mode: hybrid
  timer:
    interval: 300
  diff_threshold:
    threshold: 0.05
    check_interval: 60
    ignore_whitespace: true
    ignore_comments: false
  hybrid:
    min_interval: 180
    max_interval: 600
    threshold: 0.03
  retention:
    max_autosaves: 50
    compress_after_days: 7
    delete_after_days: 60
    keep_manual: true
diff_format:
  default: unified
  unified_context: 3
  json_include_content: true
  ast_enabled: false
output:
  default_name: '{project}_doc_{date}.md'
  include_tree: true
  include_code: true
  tree_full_code_select: false
  language_detection: true
  max_file_size: 1000000
storage_path: .gencodedoc
compression_enabled: false
compression_level: 3

```

### 📄 `.pytest_cache/.gitignore`

```text
# Created by pytest automatically.
*

```

### 📄 `.pytest_cache/CACHEDIR.TAG`

```text
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by pytest.
# For information about cache directory tags, see:
#	https://bford.info/cachedir/spec.html

```

### 📄 `.pytest_cache/README.md`

```markdown
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

```

### 📄 `.pytest_cache/v/cache/lastfailed`

```text
{}
```

### 📄 `.pytest_cache/v/cache/nodeids`

```text
[
  "tests/test_cli.py::test_config_commands",
  "tests/test_cli.py::test_doc_generate_command",
  "tests/test_cli.py::test_init_command",
  "tests/test_cli.py::test_snapshot_commands",
  "tests/test_cli.py::test_status_command",
  "tests/test_config.py::test_apply_nodejs_preset",
  "tests/test_config.py::test_apply_python_preset",
  "tests/test_config.py::test_init_project",
  "tests/test_config.py::test_load_config",
  "tests/test_config.py::test_save_config",
  "tests/test_documentation.py::test_doc_custom_output",
  "tests/test_documentation.py::test_doc_generation",
  "tests/test_mcp.py::test_execute_create_snapshot",
  "tests/test_mcp.py::test_execute_get_file_at_version",
  "tests/test_mcp.py::test_execute_list_snapshots",
  "tests/test_mcp.py::test_execute_restore_files",
  "tests/test_mcp.py::test_get_tools",
  "tests/test_mcp.py::test_set_config_value",
  "tests/test_scanner.py::test_ignore_rules",
  "tests/test_scanner.py::test_scan_files",
  "tests/test_storage.py::test_compression",
  "tests/test_storage.py::test_deduplication",
  "tests/test_storage.py::test_store_initialization",
  "tests/test_utils.py::test_file_filter",
  "tests/test_utils.py::test_tree_generator",
  "tests/test_versioning.py::test_create_snapshot",
  "tests/test_versioning.py::test_get_snapshot",
  "tests/test_versioning.py::test_list_snapshots",
  "tests/test_versioning.py::test_partial_restore",
  "tests/test_versioning.py::test_restore_snapshot"
]
```

### 📄 `.pytest_cache/v/cache/stepwise`

```text
[]
```

### 📄 `LICENSE`

```text
MIT License

Copyright (c) 2023 GencodeDoc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```

### 📄 `Makefile`

```makefile
.PHONY: help install install-dev test test-cov test-watch lint format clean clean-cache dev shell docs serve-mcp demo info all

# Variables
PROJECT_DIR := $(shell pwd)
VENV_DIR := $(shell poetry env info --path 2>/dev/null || echo ".venv")
CACHE_DIR := $(shell poetry config cache-dir 2>/dev/null || echo "~/.cache/pypoetry")

PYTHON := poetry run python
PYTEST := poetry run pytest
BLACK := poetry run black
RUFF := poetry run ruff

help: ## 📚 Afficher l'aide
	@echo "🚀 GenCodeDoc - Commandes disponibles :"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Astuce : Utilise 'make <commande>' pour exécuter"

install: ## 📥 Installer les dépendances
	poetry install

install-dev: ## 📥 Installer avec dépendances de dev
	poetry install --with dev

test: ## 🧪 Lancer les tests
	$(PYTEST) -v

test-cov: ## 📊 Tests avec couverture
	$(PYTEST) --cov=gencodedoc --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "📊 Rapport HTML généré dans : htmlcov/index.html"

test-watch: ## 👀 Tests en mode watch
	$(PYTEST) -v --watch

lint: ## 🔍 Vérifier le code (ruff + mypy)
	@echo "🔍 Vérification avec Ruff..."
	-$(RUFF) check gencodedoc/
	@echo ""
	@echo "🔍 Vérification des types avec mypy..."
	-poetry run mypy gencodedoc/ --ignore-missing-imports

format: ## ✨ Formater le code
	@echo "✨ Formatage avec Black..."
	$(BLACK) gencodedoc/ tests/
	@echo ""
	@echo "✨ Auto-fix avec Ruff..."
	$(RUFF) check --fix gencodedoc/
	@echo ""
	@echo "✅ Code formaté !"

clean: ## 🧹 Nettoyer les fichiers temporaires
	@echo "🧹 Nettoyage en cours..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .pytest_cache .coverage htmlcov/ .ruff_cache .mypy_cache
	@echo "✅ Nettoyage terminé !"

clean-cache: ## 🗑️  Vider le cache Poetry (sur NTFS)
	@echo "📊 Cache Poetry : $(CACHE_DIR)"
	@du -sh $(CACHE_DIR) 2>/dev/null || echo "Cache vide"
	@echo ""
	@read -p "Vider le cache ? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		poetry cache clear . --all; \
		echo "✅ Cache vidé !"; \
	else \
		echo "❌ Annulé"; \
	fi

dev: ## 🔧 Afficher comment activer le venv
	@echo "🔧 Pour activer le venv :"
	@echo ""
	@echo "  source $$(poetry env info --path)/bin/activate"
	@echo ""
	@echo "Ou utilise directement :"
	@echo "  make shell"

shell: ## 🐚 Lancer un shell dans le venv
	@echo "🐚 Lancement du shell dans le venv..."
	@echo "   (tape 'exit' pour quitter)"
	@poetry run bash || poetry run sh

docs: ## 📝 Générer la documentation
	@echo "📝 Génération de la documentation..."
	poetry run gencodedoc doc generate
	@echo "✅ Documentation générée !"

serve-mcp: ## 🔌 Lancer le serveur MCP
	@echo "🔌 Démarrage du serveur MCP..."
	poetry run gencodedoc mcp serve --reload
serve-mcp-stdio: ## 🔌 Lancer le serveur MCP stdio
	@echo "🔌 Démarrage du serveur MCP (stdio)..."
	poetry run python -m gencodedoc.mcp.server_stdio

serve-mcp-sse: ## 🔌 Lancer le serveur MCP SSE
	@echo "🔌 Démarrage du serveur MCP (SSE)..."
	@echo "   URL: http://127.0.0.1:8000"
	poetry run python -m gencodedoc.mcp.server_sse

test-mcp-stdio: ## 🧪 Tester le serveur stdio
	@echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | poetry run python -m gencodedoc.mcp.server_stdio

test-mcp-sse: ## 🧪 Tester le serveur SSE
	@echo "🧪 Test du serveur SSE..."
	@curl -s http://127.0.0.1:8000/mcp/tools | jq .
demo: ## 🎬 Démonstration rapide
	@echo "🎬 GenCodeDoc - Démonstration"
	@echo ""
	poetry run gencodedoc init --preset python
	poetry run gencodedoc snapshot create -m "Demo snapshot"
	poetry run gencodedoc doc generate
	poetry run gencodedoc status

info: ## 📊 Informations sur l'installation
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 INFORMATIONS GENCODEDOC"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📂 Structure :"
	@echo "  Code      : $(PROJECT_DIR)"
	@echo "  Venv      : $$(poetry env info --path 2>/dev/null || echo 'Non installé')"
	@echo "  Cache     : $(CACHE_DIR)"
	@echo ""
	@echo "💾 Espace disque :"
	@echo "  Code      : $$(du -sh $(PROJECT_DIR) 2>/dev/null | cut -f1)"
	@echo "  Venv      : $$(du -sh $$(poetry env info --path 2>/dev/null) 2>/dev/null | cut -f1 || echo 'N/A')"
	@echo "  Cache     : $$(du -sh $(CACHE_DIR) 2>/dev/null | cut -f1 || echo 'N/A')"
	@echo ""
	@echo "🖥️  Partitions :"
	@df -h / | head -1
	@df -h / | grep -E '/$$' || df -h / | tail -1
	@echo ""
	@df -h $(VENV_DIR) | head -1
	@df -h $(VENV_DIR) | tail -1
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

all: format lint test ## ✅ Tout vérifier avant commit
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Vérification complète terminée !"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

```

### 📄 `README.md`

```markdown
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

```

### 📄 `cleanup_sqlite3.sh`

```bash
#!/bin/bash
rm -f /home/fkomp/Bureau/oracle/utilitaires/gencodedoc/gencodedoc/sqlite3
echo "Removed sqlite3 if it existed"

```

### 📄 `gencodedoc/__init__.py`

```python
"""
gencodedoc - Smart documentation generator and intelligent versioning system
"""

__version__ = "2.1.0"
__author__ = "Your Name"
__license__ = "MIT"

import os
import logging

# Configure logging based on GENCODEDOC_DEBUG
log_level = logging.DEBUG if os.environ.get("GENCODEDOC_DEBUG") else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from .core.config import ConfigManager
from .core.scanner import FileScanner
from .core.versioning import VersionManager
from .core.documentation import DocumentationGenerator

__all__ = [
    "ConfigManager",
    "FileScanner",
    "VersionManager",
    "DocumentationGenerator",
]

```

### 📄 `gencodedoc/__main__.py`

```python
"""Entry point for python -m gencodedoc"""
from .cli.main import app

if __name__ == "__main__":
    app()

```

### 📄 `gencodedoc/cli/__init__.py`

```python

```

### 📄 `gencodedoc/cli/config_cmd.py`

```python
"""Configuration management commands"""
import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
from typing import Optional

app = typer.Typer(help="⚙️ Configuration management")
console = Console()


@app.command("show")
def show_config(
    global_config: bool = typer.Option(False, "--global-config", help="Show global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show current configuration"""
    from ..core.config import ConfigManager
    import yaml

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)

    if global_config:
        config_path = config_manager.global_config_path
    else:
        config_path = config_manager.config_path

    if not config_path.exists():
        console.print(f"[yellow]No configuration file at {config_path}[/yellow]")
        return

    with open(config_path) as f:
        config_yaml = f.read()

    syntax = Syntax(config_yaml, "yaml", theme="monokai", line_numbers=True)
    console.print(f"\n[bold]Configuration: {config_path}[/bold]\n")
    console.print(syntax)


@app.command("edit")
def edit_config(
    global_config: bool = typer.Option(False, "--global-config", help="Edit global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Edit configuration file"""
    from ..core.config import ConfigManager
    import os

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)

    if global_config:
        config_path = config_manager.global_config_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        config_path = config_manager.config_path

    # Create if doesn't exist
    if not config_path.exists():
        config = config_manager.init_project()
        console.print(f"[green]Created new config at {config_path}[/green]")

    # Open in editor
    editor = os.environ.get('EDITOR', 'nano')
    os.system(f'{editor} {config_path}')

    console.print("[green]✅ Configuration updated[/green]")


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Config key (e.g., 'autosave.enabled')"),
    value: str = typer.Argument(..., help="Value to set"),
    global_config: bool = typer.Option(False, "--global-config", help="Set in global config"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Set a configuration value"""
    from ..core.config import ConfigManager
    import yaml

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    # Parse key path
    keys = key.split('.')

    # Navigate to nested dict
    config_dict = config.model_dump()
    target = config_dict
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    # Convert value type
    if value.lower() == 'true':
        parsed_value = True
    elif value.lower() == 'false':
        parsed_value = False
    elif value.isdigit():
        parsed_value = int(value)
    else:
        try:
            parsed_value = float(value)
        except ValueError:
            parsed_value = value

    # Set value
    target[keys[-1]] = parsed_value

    # Save
    from ..models.config import ProjectConfig
    updated_config = ProjectConfig(**config_dict)
    config_manager.save(updated_config, global_config=global_config)

    console.print(f"[green]✅ Set {key} = {parsed_value}[/green]")


@app.command("preset")
def apply_preset(
    preset: str = typer.Argument(..., help="Preset name (python, nodejs, web, go)"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Apply a configuration preset"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    config_manager._apply_preset(config, preset)
    config_manager.save(config)

    console.print(f"[green]✅ Applied preset: {preset}[/green]")


@app.command("ignore")
def manage_ignore(
    add_dir: Optional[str] = typer.Option(None, help="Add directory to ignore"),
    add_file: Optional[str] = typer.Option(None, help="Add file to ignore"),
    add_ext: Optional[str] = typer.Option(None, help="Add extension to ignore"),
    list_all: bool = typer.Option(False, help="List all ignore rules"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Manage ignore rules"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    if list_all:
        table = Table(title="Ignore Rules")
        table.add_column("Type", style="cyan")
        table.add_column("Rules", style="green")

        table.add_row("Directories", ", ".join(config.ignore.dirs))
        table.add_row("Files", ", ".join(config.ignore.files))
        table.add_row("Extensions", ", ".join(config.ignore.extensions))
        if config.ignore.patterns:
            table.add_row("Patterns", ", ".join(config.ignore.patterns))

        console.print(table)
        return

    modified = False

    if add_dir:
        if add_dir not in config.ignore.dirs:
            config.ignore.dirs.append(add_dir)
            modified = True
            console.print(f"[green]Added directory: {add_dir}[/green]")

    if add_file:
        if add_file not in config.ignore.files:
            config.ignore.files.append(add_file)
            modified = True
            console.print(f"[green]Added file: {add_file}[/green]")

    if add_ext:
        if not add_ext.startswith('.'):
            add_ext = '.' + add_ext
        if add_ext not in config.ignore.extensions:
            config.ignore.extensions.append(add_ext)
            modified = True
            console.print(f"[green]Added extension: {add_ext}[/green]")

    if modified:
        config_manager.save(config)
        console.print("[green]✅ Configuration saved[/green]")

```

### 📄 `gencodedoc/cli/doc_cmd.py`

```python
"""Documentation generation commands"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List

app = typer.Typer(help="📚 Documentation generation")
console = Console()


@app.command("generate")
def generate_doc(
    output: Optional[Path] = typer.Option(None, help="Output file path"),
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    exclude: Optional[List[str]] = typer.Option(None, help="Paths to exclude"),
    tree: bool = typer.Option(True, "--tree/--no-tree", help="Include directory tree"),
    code: bool = typer.Option(True, "--code/--no-code", help="Include file code"),
    tree_full: bool = typer.Option(False, "--tree-full/--no-tree-full", help="Full tree, selected code only"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)"),
    split_limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Split output into files of N lines"),
    ignore_tree: Optional[List[str]] = typer.Option(None, "--ignore-tree", "-i", help="Patterns to ignore in tree view")
):
    """Generate project documentation"""
    from ..core.config import ConfigManager
    from ..core.documentation import DocumentationGenerator

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    doc_gen = DocumentationGenerator(config)

    with console.status("[bold blue]Generating documentation..."):
        output_paths = doc_gen.generate(
            output_path=output,
            include_paths=include,
            exclude_paths=exclude,
            include_tree=tree,
            include_code=code,
            tree_full_code_select=tree_full,
            split_limit=split_limit,
            ignore_tree_patterns=ignore_tree
        )

    console.print(f"[green]✅ Documentation generated![/green]")
    for path in output_paths:
        file_size = path.stat().st_size / 1024
        console.print(f"   📄 {path.name} ({file_size:.1f} KB)")


@app.command("preview")
def preview_structure(
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    max_depth: Optional[int] = typer.Option(None, help="Max tree depth"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Preview project structure"""
    from ..core.config import ConfigManager
    from ..utils.tree import TreeGenerator
    from ..utils.filters import FileFilter

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    tree_gen = TreeGenerator()
    file_filter = FileFilter(config.ignore, config.project_path)

    console.print(f"[bold blue]Project Structure: {config.project_name}[/bold blue]\n")

    tree = tree_gen.generate(
        config.project_path,
        max_depth=max_depth,
        filter_func=lambda p: not file_filter.should_ignore(p, p.is_dir())
    )

    console.print(tree)


@app.command("stats")
def show_stats(
    include: Optional[List[str]] = typer.Option(None, help="Paths to include"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show project statistics"""
    from ..core.config import ConfigManager
    from ..core.scanner import FileScanner
    from ..utils.formatters import format_size
    from rich.table import Table
    from collections import Counter

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    scanner = FileScanner(config)

    with console.status("[bold blue]Scanning project..."):
        files = scanner.scan(include_paths=include)

    # Calculate stats
    total_size = sum(f.size for f in files)
    extensions = Counter(Path(f.path).suffix for f in files)

    # Summary table
    summary = Table(title="Project Statistics")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green", justify="right")

    summary.add_row("Total Files", str(len(files)))
    summary.add_row("Total Size", format_size(total_size))
    summary.add_row("Unique Extensions", str(len(extensions)))

    console.print(summary)

    # Extensions table
    if extensions:
        ext_table = Table(title="Files by Extension")
        ext_table.add_column("Extension", style="cyan")
        ext_table.add_column("Count", style="green", justify="right")
        ext_table.add_column("Percentage", style="yellow", justify="right")

        for ext, count in extensions.most_common(10):
            ext_name = ext if ext else "(no extension)"
            percentage = (count / len(files)) * 100
            ext_table.add_row(ext_name, str(count), f"{percentage:.1f}%")

        console.print("\n")
        console.print(ext_table)

```

### 📄 `gencodedoc/cli/main.py`

```python
"""Main CLI entry point"""
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="gencodedoc",
    help="🚀 Documentation generator and intelligent versioning system",
    add_completion=False,
    no_args_is_help=True
)

console = Console()

# Import des sous-commandes
from . import snapshot_cmd, doc_cmd, config_cmd, mcp_cmd, tree_cmd

app.add_typer(snapshot_cmd.app, name="snapshot")
app.add_typer(doc_cmd.app, name="doc")
app.add_typer(config_cmd.app, name="config")
app.add_typer(mcp_cmd.app, name="mcp")
app.add_typer(tree_cmd.app, name="viz")  # 'tree' is often expected as a direct command, but here we add it as subcommand or direct

# Direct command registration for 'tree'
from .tree_cmd import tree_command
app.command("tree")(tree_command)


@app.command()
def init(
    preset: Optional[str] = typer.Option(None, help="Configuration preset (python, nodejs, go, web)"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """🎬 Initialize gencodedoc in a project"""
    from ..core.config import ConfigManager

    project_path = Path(path) if path else Path.cwd()

    console.print(f"[bold blue]Initializing gencodedoc in {project_path}[/bold blue]")

    try:
        config_manager = ConfigManager(project_path)
        config = config_manager.init_project()

        if preset:
            config_manager._apply_preset(config, preset)
            config_manager.save(config)

        # Create storage directory
        storage_path = project_path / config.storage_path
        storage_path.mkdir(exist_ok=True)

        console.print(f"[green]✅ Project initialized![/green]")
        console.print(f"   Config: {config_manager.config_path}")
        console.print(f"   Storage: {storage_path}")

        if preset:
            console.print(f"   Preset: {preset}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """📊 Show project status"""
    from ..core.config import ConfigManager
    from ..storage.database import Database

    project_path = Path(path) if path else Path.cwd()

    try:
        config_manager = ConfigManager(project_path)
        config = config_manager.load()

        db_path = project_path / config.storage_path / "gencodedoc.db"

        if not db_path.exists():
            console.print("[yellow]⚠️  No snapshots yet. Run 'gencodedoc init' first.[/yellow]")
            return

        db = Database(db_path)
        snapshots = db.list_snapshots(limit=5)

        # Summary table
        table = Table(title="Project Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Project", config.project_name or project_path.name)
        table.add_row("Path", str(config.project_path))
        table.add_row("Total Snapshots", str(len(db.list_snapshots())))
        table.add_row("Autosave", "✅ Enabled" if config.autosave.enabled else "❌ Disabled")

        console.print(table)

        # Recent snapshots
        if snapshots:
            console.print("\n[bold]Recent Snapshots:[/bold]")
            snap_table = Table()
            snap_table.add_column("ID", style="cyan")
            snap_table.add_column("Date", style="magenta")
            snap_table.add_column("Message", style="green")
            snap_table.add_column("Type", style="yellow")

            for snap in snapshots[:5]:
                snap_table.add_row(
                    str(snap['id']),
                    snap['created_at'],
                    snap['message'] or "(no message)",
                    "auto" if snap['is_autosave'] else "manual"
                )

            console.print(snap_table)

    except FileNotFoundError:
        console.print("[yellow]⚠️  Project not initialized. Run 'gencodedoc init' first.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

```

### 📄 `gencodedoc/cli/mcp_cmd.py`

```python
"""MCP server commands"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional

app = typer.Typer(help="🔌 MCP server")
console = Console()


@app.command("serve")
def serve_mcp(
    host: Optional[str] = typer.Option(None, help="Host to bind to (default: 127.0.0.1)"),
    port: Optional[int] = typer.Option(None, help="Port to bind to (default: 8000)"),
    reload: bool = typer.Option(False, help="Auto-reload on code changes"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Start MCP server"""
    from ..mcp.server import create_app
    import uvicorn

    # Valeurs par défaut
    actual_host = host if host else "127.0.0.1"
    actual_port = port if port else 8000
    project_path = Path(path) if path else Path.cwd()

    console.print(f"[bold blue]Starting MCP server...[/bold blue]")
    console.print(f"   Host: {actual_host}")
    console.print(f"   Port: {actual_port}")
    console.print(f"   Project: {project_path}")

    app_instance = create_app(project_path)

    uvicorn.run(
        app_instance,
        host=actual_host,
        port=actual_port,
        reload=reload,
        log_level="info"
    )


@app.command("tools")
def list_tools():
    """List available MCP tools"""
    from ..mcp.tools import get_tools_definition
    from rich.table import Table

    tools = get_tools_definition()

    table = Table(title="Available MCP Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for tool in tools:
        table.add_row(tool["name"], tool["description"])

    console.print(table)


@app.command("config-claude")
def config_claude(
    port: Optional[int] = typer.Option(None, help="MCP server port (default: 8000)")
):
    """Generate Claude Desktop MCP configuration"""
    import json

    actual_port = port if port else 8000

    config = {
        "mcpServers": {
            "gencodedoc": {
                "url": f"http://127.0.0.1:{actual_port}/mcp",
                "description": "GenCodeDoc - Smart documentation and versioning"
            }
        }
    }

    console.print("[bold]Add this to your Claude Desktop configuration:[/bold]\n")
    console.print(json.dumps(config, indent=2))

    # Platform-specific paths
    import platform
    system = platform.system()

    console.print("\n[bold]Configuration file location:[/bold]")
    if system == "Darwin":  # macOS
        console.print("  ~/Library/Application Support/Claude/claude_desktop_config.json")
    elif system == "Windows":
        console.print("  %APPDATA%\\Claude\\claude_desktop_config.json")
    else:  # Linux
        console.print("  ~/.config/Claude/claude_desktop_config.json")

```

### 📄 `gencodedoc/cli/snapshot_cmd.py`

```python
"""Snapshot management commands"""
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from typing import Optional, List

app = typer.Typer(help="📸 Snapshot management")
console = Console()


@app.command("create")
def create_snapshot(
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Snapshot message"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Tag for easy reference"),
    include: Optional[List[str]] = typer.Option(None, "--include", "-i", help="Paths to include"),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", "-x", help="Paths to exclude"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Create a new snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status("[bold blue]Creating snapshot..."):
        snapshot = version_manager.create_snapshot(
            message=message,
            tag=tag,
            include_paths=include,
            exclude_paths=exclude
        )

    console.print(f"[green]✅ Snapshot created![/green]")
    console.print(f"   ID: {snapshot.metadata.id}")
    console.print(f"   Files: {snapshot.metadata.files_count}")
    console.print(f"   Size: {snapshot.metadata.total_size / 1024:.1f} KB")
    if tag:
        console.print(f"   Tag: {tag}")


@app.command("list")
def list_snapshots(
    limit: int = typer.Option(10, help="Max snapshots to show"),
    all: bool = typer.Option(False, "--all", help="Include autosaves"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """List snapshots"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_date, format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    snapshots = version_manager.list_snapshots(limit=limit, include_autosave=all)

    if not snapshots:
        console.print("[yellow]No snapshots found[/yellow]")
        return

    table = Table(title=f"Snapshots ({len(snapshots)})")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="magenta")
    table.add_column("Tag", style="yellow")
    table.add_column("Message", style="green")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Type", style="blue")

    for snap in snapshots:
        table.add_row(
            str(snap.metadata.id),
            format_date(snap.metadata.created_at, "%Y-%m-%d %H:%M"),
            snap.metadata.tag or "-",
            snap.metadata.message or "-",
            str(snap.metadata.files_count),
            format_size(snap.metadata.total_size),
            "auto" if snap.metadata.is_autosave else "manual"
        )

    console.print(table)


@app.command("show")
def show_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Show snapshot details"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_date, format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    snapshot = version_manager.get_snapshot(snapshot_ref)

    if not snapshot:
        console.print(f"[red]Snapshot '{snapshot_ref}' not found[/red]")
        raise typer.Exit(1)

    # Metadata table
    table = Table(title=f"Snapshot {snapshot.metadata.id}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("ID", str(snapshot.metadata.id))
    table.add_row("Date", format_date(snapshot.metadata.created_at))
    if snapshot.metadata.tag:
        table.add_row("Tag", snapshot.metadata.tag)
    if snapshot.metadata.message:
        table.add_row("Message", snapshot.metadata.message)
    table.add_row("Type", "autosave" if snapshot.metadata.is_autosave else "manual")
    table.add_row("Trigger", snapshot.metadata.trigger_type)
    table.add_row("Files", str(snapshot.metadata.files_count))
    table.add_row("Total Size", format_size(snapshot.metadata.total_size))
    table.add_row("Compressed", format_size(snapshot.metadata.compressed_size))

    console.print(table)

    # Files list
    console.print("\n[bold]Files:[/bold]")
    for file_entry in snapshot.files[:20]:  # Show first 20
        console.print(f"  • {file_entry.path}")

    if len(snapshot.files) > 20:
        console.print(f"  ... and {len(snapshot.files) - 20} more")


@app.command("restore")
def restore_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Glob patterns for partial restore"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Restore a snapshot (full or partial)"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    partial = " (partial)" if filter else ""
    if not force:
        confirm = typer.confirm(
            f"This will restore snapshot '{snapshot_ref}'{partial}. Continue?",
            default=False
        )
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    with console.status(f"[bold blue]Restoring snapshot {snapshot_ref}..."):
        result = version_manager.restore_snapshot(
            snapshot_ref, force=force, file_filters=filter
        )

    console.print(f"[green]✅ Snapshot restored{partial}![/green]")
    console.print(f"   Restored: {result['restored_count']}/{result['total_files']} files")
    if result['skipped_count'] > 0:
        console.print(f"   Skipped: {result['skipped_count']} files")


@app.command("diff")
def diff_snapshots(
    from_ref: str = typer.Argument(..., help="Source snapshot"),
    to_ref: str = typer.Argument("current", help="Target snapshot or 'current'"),
    format: str = typer.Option("unified", help="Diff format (unified/json)"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Filter diff to specific files/patterns"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Compare two snapshots, optionally filtered to specific files"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..core.differ import DiffGenerator

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status("[bold blue]Calculating diff..."):
        diff = version_manager.diff_snapshots(from_ref, to_ref, file_filters=filter)

        differ = DiffGenerator(config.diff_format, version_manager.store)
        diff_output = differ.generate_diff(diff, format=format)

    if filter:
        console.print(f"[dim]🔍 Filtered: {', '.join(filter)}[/dim]")
    
    # Rich syntax highlighting for diff
    from rich.syntax import Syntax
    from rich.panel import Panel
    
    syntax = Syntax(diff_output, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"📊 Diff: {from_ref} → {to_ref}", border_style="blue"))


@app.command("delete")
def delete_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Delete a snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    if not force:
        confirm = typer.confirm(
            f"Delete snapshot '{snapshot_ref}'?",
            default=False
        )
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    success = version_manager.delete_snapshot(snapshot_ref)

    if success:
        console.print("[green]✅ Snapshot deleted[/green]")
    else:
        console.print("[red]❌ Snapshot not found[/red]")
        raise typer.Exit(1)


@app.command("cat")
def cat_file_at_version(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    file_path: str = typer.Argument(..., help="Relative path of the file"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """View file content at a specific version"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from rich.syntax import Syntax
    from ..utils.formatters import get_language_from_extension

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    try:
        content = version_manager.get_file_content_at_version(snapshot_ref, file_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if content is None:
        console.print(f"[red]Could not retrieve content for '{file_path}'[/red]")
        raise typer.Exit(1)

    lang = get_language_from_extension(file_path)
    syntax = Syntax(content, lang, line_numbers=True, theme="monokai")
    console.print(f"\n[bold]📄 {file_path} @ {snapshot_ref}[/bold]\n")
    console.print(syntax)


@app.command("files")
def list_files_at_version(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    pattern: Optional[str] = typer.Option(None, help="Glob pattern to filter"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """List files in a snapshot"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    try:
        files = version_manager.list_files_at_version(snapshot_ref, pattern=pattern)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Files in snapshot {snapshot_ref} ({len(files)})")
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for f in files:
        table.add_row(f['path'], format_size(f['size']))

    console.print(table)


@app.command("export")
def export_snapshot(
    snapshot_ref: str = typer.Argument(..., help="Snapshot ID or tag"),
    output: str = typer.Argument(..., help="Output folder or archive path (.tar.gz)"),
    archive: bool = typer.Option(False, "--archive", help="Create .tar.gz archive"),
    filter: Optional[List[str]] = typer.Option(None, "--filter", help="Glob patterns to filter files"),
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Export a snapshot to a folder or archive"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager
    from ..utils.formatters import format_size

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)

    with console.status(f"[bold blue]Exporting snapshot {snapshot_ref}..."):
        result = version_manager.export_snapshot(
            snapshot_ref=snapshot_ref,
            output_path=Path(output),
            archive=archive,
            file_filters=filter
        )

    console.print(f"[green]✅ Snapshot exported![/green]")
    console.print(f"   Format: {result['format']}")
    console.print(f"   Output: {result['output_path']}")
    console.print(f"   Files: {result['exported_count']}")
    if result.get('archive_size'):
        console.print(f"   Archive size: {format_size(result['archive_size'])}")
    if result['failed_count'] > 0:
        console.print(f"   [yellow]⚠️ {result['failed_count']} files failed[/yellow]")


@app.command("cleanup")
def cleanup_orphaned(
    path: Optional[str] = typer.Option(None, help="Project path (default: current directory)")
):
    """Remove orphaned file contents from the database"""
    from ..core.config import ConfigManager
    from ..core.versioning import VersionManager

    project_path = Path(path) if path else Path.cwd()
    config_manager = ConfigManager(project_path)
    config = config_manager.load()

    version_manager = VersionManager(config)
    count = version_manager.cleanup_orphaned_contents()

    console.print(f"[green]🧹 Removed {count} orphaned content(s)[/green]")

```

### 📄 `gencodedoc/cli/tree_cmd.py`

```python
"""Tree visualization command"""
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List
import copy

app = typer.Typer(help="🌳 Project structure visualization")
console = Console()

@app.command("tree")
def tree_command(
    path: Optional[str] = typer.Argument(None, help="Path to directory (default: current)"),
    depth: Optional[int] = typer.Option(None, "--depth", "-d", help="Maximum depth"),
    all: bool = typer.Option(False, "--all", "-a", help="Show hidden files"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(50, "--limit", "-l", help="Lines per page"),
    ignore: Optional[List[str]] = typer.Option(None, "--ignore", "-i", help="Add ignore patterns"),
    paginate: bool = typer.Option(True, help="Enable pagination (default: True)")
):
    """Show project structure tree"""
    from ..core.config import ConfigManager
    from ..utils.tree import TreeGenerator
    from ..utils.filters import FileFilter

    target_path = Path(path) if path else Path.cwd()
    
    # Load config for ignores
    try:
        config_manager = ConfigManager(target_path)
        config = config_manager.load()
        ignore_config = config.ignore
    except Exception:
        # Fallback if not a project
        from ..models.config import IgnoreConfig
        ignore_config = IgnoreConfig()
        config = None

    # Apply ad-hoc ignores
    if ignore:
        # Create a deep copy to avoid modifying global config if loaded
        ignore_config = copy.deepcopy(ignore_config)
        for pattern in ignore:
            if pattern.startswith('.'):
                ignore_config.extensions.append(pattern)
            elif '/' in pattern or '*' in pattern:
                ignore_config.patterns.append(pattern)
            else:
                ignore_config.files.append(pattern)
                ignore_config.dirs.append(pattern)

    tree_gen = TreeGenerator(show_hidden=all)
    file_filter = FileFilter(ignore_config, target_path)

    start_func = lambda p: not file_filter.should_ignore(p, p.is_dir())

    tree = tree_gen.generate(
        target_path,
        max_depth=depth,
        filter_func=start_func,
        paginate=paginate,
        page=page,
        limit=limit
    )

    console.print(f"[bold blue]📁 Project: {target_path.name}[/bold blue]")
    if paginate:
        console.print(f"[dim](Page {page}, {limit} lines/page)[/dim]")
    
    console.print(tree)

```

### 📄 `gencodedoc/config/presets/go.yaml`

```yaml
ignore:
  dirs:
    - vendor
    - bin
    - .git
  extensions:
    - .exe
    - .test
    - .out

```

### 📄 `gencodedoc/config/presets/nodejs.yaml`

```yaml
ignore:
  dirs:
    - node_modules
    - dist
    - build
    - coverage
    - .git
    - .next
    - .nuxt
    - .output
  files:
    - package-lock.json
    - yarn.lock
    - pnpm-lock.yaml
    - .DS_Store
    - .env

```

