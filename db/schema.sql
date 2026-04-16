-- =============================================================
-- Méthode Cerise Modulaire — Registre MCP
-- Chaque module est autonome (cerise), l'ensemble forme l'arbre
-- =============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─────────────────────────────────────────────────────────────
-- TABLE 1 : MCP Servers
-- Registre de tous les serveurs MCP disponibles dans le système
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mcp_servers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    transport   TEXT    NOT NULL DEFAULT 'stdio' CHECK (transport IN ('stdio','http','sse')),
    command     TEXT,                          -- ex: "python3" ou "npx"
    args        TEXT    DEFAULT '[]',          -- JSON array d'arguments
    env_vars    TEXT    DEFAULT '{}',          -- JSON object des vars d'env requises
    is_active   INTEGER NOT NULL DEFAULT 1,
    version     TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- TABLE 2 : Tools
-- Fonctions appelables exposées par chaque serveur MCP
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tools (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id    INTEGER NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    name         TEXT    NOT NULL,
    description  TEXT,
    input_schema TEXT    DEFAULT '{}',  -- JSON Schema des paramètres d'entrée
    output_type  TEXT    DEFAULT 'text' CHECK (output_type IN ('text','json','image','mixed')),
    is_active    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    DEFAULT (datetime('now')),
    UNIQUE (server_id, name)
);

-- ─────────────────────────────────────────────────────────────
-- TABLE 3 : Resources
-- Données accessibles en lecture via URI MCP
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id   INTEGER NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
    uri         TEXT    NOT NULL,             -- ex: "jobs://latest-summary"
    name        TEXT    NOT NULL,
    description TEXT,
    mime_type   TEXT    DEFAULT 'text/plain',
    is_template INTEGER NOT NULL DEFAULT 0,   -- 1 = URI avec paramètres {var}
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE (server_id, uri)
);

-- ─────────────────────────────────────────────────────────────
-- TABLE 4 : Prompt Templates
-- Structures de prompts réutilisables par tâche
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prompt_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id   INTEGER REFERENCES mcp_servers(id) ON DELETE SET NULL,
    name        TEXT    NOT NULL UNIQUE,
    title       TEXT,
    role        TEXT    NOT NULL DEFAULT 'user' CHECK (role IN ('system','user','assistant')),
    template    TEXT    NOT NULL,             -- texte avec {{variables}} Jinja-style
    variables   TEXT    DEFAULT '[]',         -- JSON array des noms de variables
    task_type   TEXT,                         -- extraction | classification | matching | search
    model_hint  TEXT,                         -- modèle recommandé pour ce prompt
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- INDEX
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tools_server     ON tools(server_id);
CREATE INDEX IF NOT EXISTS idx_resources_server ON resources(server_id);
CREATE INDEX IF NOT EXISTS idx_prompts_task     ON prompt_templates(task_type);
