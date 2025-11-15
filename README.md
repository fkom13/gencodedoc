<!-- mcp-name: io.github.fkom13/gencodedoc -->
# 🚀 GenCodeDoc

<div align="center">

**Système de versioning intelligent et générateur de documentation, avec support complet du protocole MCP.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-poetry-blueviolet)](https://python-poetry.org/)
[![MCP Compatible](https://img.shields.io/badge/MCP-stdio%20%7C%20SSE%20%7C%20REST-green)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Un outil de versioning et de documentation intelligent pour les workflows de développement modernes.*

</div>

---

GenCodeDoc est un outil puissant qui réinvente la manière de suivre l'évolution d'un projet de code. Il combine un système de **snapshots intelligents** avec déduplication, un **générateur de documentation Markdown**, et une **interface complète (CLI, API REST, MCP)** pour l'automatisation et l'intégration avec des assistants IA.

Pour une documentation technique détaillée (architecture, API complète, etc.), consultez notre [**GUIDE COMPLET**](DOCUMENTATION.md).

## ✨ Fonctionnalités Principales

-   📸 **Snapshots Intelligents** : Créez des "photographies" de votre projet avec une économie d'espace de ~70% grâce à la déduplication de contenu par hash.
-   🔄 **Autosave Intelligent** : Protégez votre travail avec 3 modes d'enregistrement automatique (basé sur le temps, les changements, ou un mode hybride).
-   📝 **Documentation Automatisée** : Générez une documentation Markdown complète de votre projet, incluant l'arborescence des fichiers et des extraits de code.
-   🔍 **Diff Avancé** : Comparez n'importe quelles versions de votre projet avec un diff unifié (style Git), JSON (pour les scripts) ou sémantique (AST, expérimental).
-   🔌 **Triple Interface** : Utilisez GenCodeDoc de la manière qui vous convient le mieux :
    -   **CLI** : Une interface en ligne de commande complète et intuitive.
    -   **API REST** : Intégrez GenCodeDoc dans vos propres applications via HTTP.
    -   **MCP** : Pilotez l'outil avec une IA (Gemini, Claude) grâce à 17 outils exposés via le Model-Context-Protocol.

---

## 📦 Installation

### Prérequis

-   Python 3.10+
-   [Poetry](https://python-poetry.org/) pour la gestion des dépendances.

### Étapes d'installation

1.  **Clonez le dépôt :**
    ```bash
    git clone https://github.com/VOTRE_NOM/gencodedoc.git
    cd gencodedoc
    ```

2.  **Installez les dépendances avec Poetry :**
    ```bash
    poetry install
    ```

3.  **Vérifiez l'installation :**
    ```bash
    poetry run gencodedoc --help
    ```

---

## ⚡ Guide de Démarrage Rapide

Une fois installé, voici comment démarrer avec un projet existant :

1.  **Initialisez GenCodeDoc dans votre projet :**
    ```bash
    # Naviguez vers votre projet
    cd /path/to/your/project

    # Initialisez avec un preset (ex: python)
    poetry run gencodedoc init --preset python
    ```
    *Presets disponibles : `python`, `nodejs`, `go`, `web`.*

2.  **Créez votre premier snapshot :**
    ```bash
    poetry run gencodedoc snapshot create --message "Version initiale du projet" --tag v1.0
    ```

3.  **Générez la documentation :**
    ```bash
    poetry run gencodedoc doc generate --output "PROJECT_DOCS.md"
    ```
    *Un fichier `PROJECT_DOCS.md` sera créé avec la documentation complète.*

4.  **(Optionnel) Activez l'autosave :**
    ```bash
    poetry run gencodedoc config set autosave.enabled true
    ```

---

## 🔌 Intégration MCP (Pour les Assistants IA)

GenCodeDoc est conçu pour être piloté par des IA. Il expose ses 17 outils via 3 modes de transport.

-   **`stdio`** : Pour les clients CLI comme **Gemini CLI**.
-   **`SSE`** (Server-Sent Events) : Pour les applications web ou de bureau comme **Claude Desktop**.
-   **`REST`** : Pour toute intégration personnalisée via une API HTTP.

### Configuration pour Gemini CLI (stdio)

1.  **Trouvez le chemin de votre environnement virtuel Poetry :**
    ```bash
    # Depuis le dossier de gencodedoc
    poetry env info --path 
    # Copiez le chemin retourné
    ```

2.  **Ajoutez le serveur à la configuration de votre client MCP :**
    *(Exemple pour `gemini-cli`)*
    ```json
    {
      "mcpServers": {
        "gencodedoc": {
          "command": "/path/to/your/poetry-venv/bin/python",
          "args": ["-m", "gencodedoc.mcp.server_stdio"],
          "env": {
            "PROJECT_PATH": "/path/to/your/target-project"
          }
        }
      }
    }
    ```
    *Remplacez `/path/to/your/poetry-venv` par le chemin de l'étape 1 et `PROJECT_PATH` par le projet que vous voulez gérer.*

### Démarrer les serveurs SSE / REST

```bash
# Pour le serveur SSE (Claude Desktop)
poetry run python -m gencodedoc.mcp.server_sse

# Pour le serveur REST
poetry run python -m gencodedoc.mcp.server
```
*Les deux serveurs fonctionnent sur `http://127.0.0.1:8000`.*

---

## 🧰 Référence des Outils

GenCodeDoc offre une CLI complète et une API MCP/REST riche.

### Commandes CLI Principales

-   `gencodedoc init` : Initialise un projet.
-   `gencodedoc snapshot create|list|show|diff|restore|delete` : Gère les snapshots.
-   `gencodedoc doc generate|preview|stats` : Gère la documentation.
-   `gencodedoc config show|edit|set|preset|ignore` : Gère la configuration.
-   `gencodedoc status` : Affiche l'état actuel du projet.

### Outils MCP (17 outils)

Un résumé des outils disponibles pour les IA :

-   **Gestion des Snapshots (6 outils)** : `create_snapshot`, `list_snapshots`, `get_snapshot_details`, `restore_snapshot`, `delete_snapshot`, `diff_versions`.
-   **Documentation (3 outils)** : `generate_documentation`, `preview_structure`, `get_project_stats`.
-   **Gestion de Projet (2 outils)** : `init_project`, `get_project_status`.
-   **Configuration (3 outils)** : `get_config`, `set_config_value`, `apply_preset`, `manage_ignore_rules`.
-   **Autosave (3 outils)** : `start_autosave`, `stop_autosave`, `get_autosave_status`.

Une fois configuré, vous pouvez simplement demander à votre IA :
> *"Crée un snapshot avec le tag v2.1 et le message 'Correction du bug de connexion'"*
> *"Montre-moi les différences entre la version v2.0 et la version actuelle"*
> *"Génère la documentation complète du projet"*

---

## 🏗️ Architecture et Fonctionnement

GenCodeDoc est construit autour d'un noyau logique qui gère la configuration, le versioning et la génération de documents. Ce noyau est exposé via différentes interfaces (CLI, MCP).

Le stockage est optimisé pour être à la fois performant et économe en espace :
-   **SQLite** est utilisé pour stocker toutes les métadonnées (snapshots, fichiers, etc.).
-   Le contenu des fichiers est **dédupliqué** via un hash SHA256. Un même fichier, même présent dans 100 snapshots, n'est stocké qu'une seule fois.
-   Les contenus sont ensuite **compressés** avec `zstandard` pour réduire encore plus l'empreinte disque.

---

## 🤝 Contribution

Les contributions sont les bienvenues !
1.  Forkez le projet.
2.  Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-super-feature`).
3.  Commitez vos changements (`git commit -m 'Ajout de ma super feature'`).
4.  Poussez votre branche (`git push origin feature/ma-super-feature`).
5.  Ouvrez une Pull Request.

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) for pour plus de détails.
