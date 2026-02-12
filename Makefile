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
