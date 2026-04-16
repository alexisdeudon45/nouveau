-- =============================================================
-- Données initiales — Méthode Cerise Modulaire
-- =============================================================

-- ─── MCP Servers ─────────────────────────────────────────────

INSERT OR IGNORE INTO mcp_servers (name, description, transport, command, args, env_vars, version) VALUES
(
    'jobspy',
    'Recherche d''offres d''emploi en temps réel via LinkedIn, Indeed, Glassdoor',
    'stdio',
    'python3',
    '["-m", "mcp.jobspy_server"]',
    '{"HUGGINGFACE_TOKEN": "required"}',
    '1.0.0'
),
(
    'mcp-compass',
    'Découverte et recommandation de serveurs MCP via registre mcphub.io',
    'stdio',
    'npx',
    '["-y", "@liuyoshio/mcp-compass"]',
    '{}',
    '1.0.7'
),
(
    'filesystem-pipeline',
    'Lecture/écriture de fichiers locaux — PDF, JSON, Markdown',
    'stdio',
    'npx',
    '["-y", "@modelcontextprotocol/server-filesystem"]',
    '{}',
    '0.6.2'
),
(
    'sequential-thinking',
    'Raisonnement structuré en chaîne d''étapes pour tâches complexes',
    'stdio',
    'npx',
    '["-y", "@modelcontextprotocol/server-sequential-thinking"]',
    '{}',
    '0.6.2'
),
(
    'playwright',
    'Navigation web headless — scraping LinkedIn, Glassdoor, sites RH',
    'stdio',
    'npx',
    '["-y", "@playwright/mcp"]',
    '{}',
    '0.0.28'
);

-- ─── Tools ───────────────────────────────────────────────────

INSERT OR IGNORE INTO tools (server_id, name, description, input_schema, output_type) VALUES
-- jobspy
(
    (SELECT id FROM mcp_servers WHERE name='jobspy'),
    'search_jobs',
    'Recherche des offres d''emploi sur LinkedIn, Indeed, Glassdoor avec filtres géographiques et salariaux',
    '{
        "type": "object",
        "required": ["search_term"],
        "properties": {
            "search_term":    {"type": "string",  "description": "Intitulé du poste"},
            "location":       {"type": "string",  "description": "Ville ou pays", "default": "France"},
            "results_wanted": {"type": "integer", "description": "Nombre de résultats", "default": 10},
            "hours_old":      {"type": "integer", "description": "Ancienneté max en heures", "default": 168},
            "job_type":       {"type": "string",  "enum": ["fulltime","parttime","internship","contract"]},
            "is_remote":      {"type": "boolean", "default": false},
            "min_salary":     {"type": "integer", "description": "Salaire annuel minimum"}
        }
    }',
    'json'
),
-- mcp-compass
(
    (SELECT id FROM mcp_servers WHERE name='mcp-compass'),
    'recommend-mcp-servers',
    'Recommande des serveurs MCP existants selon une description en langage naturel',
    '{
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "Description du besoin, ex: MCP Server for AWS Lambda deployment"}
        }
    }',
    'json'
),
-- filesystem-pipeline
(
    (SELECT id FROM mcp_servers WHERE name='filesystem-pipeline'),
    'read_file',
    'Lit le contenu d''un fichier local (PDF, JSON, texte)',
    '{"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}}}',
    'text'
),
(
    (SELECT id FROM mcp_servers WHERE name='filesystem-pipeline'),
    'write_file',
    'Écrit un fichier local',
    '{"type": "object", "required": ["path","content"], "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}',
    'text'
),
-- sequential-thinking
(
    (SELECT id FROM mcp_servers WHERE name='sequential-thinking'),
    'sequentialthinking',
    'Décompose un problème complexe en étapes de raisonnement traçables',
    '{
        "type": "object",
        "required": ["thought"],
        "properties": {
            "thought":          {"type": "string"},
            "nextThoughtNeeded": {"type": "boolean"},
            "thoughtNumber":    {"type": "integer"},
            "totalThoughts":    {"type": "integer"}
        }
    }',
    'json'
),
-- playwright
(
    (SELECT id FROM mcp_servers WHERE name='playwright'),
    'browser_navigate',
    'Navigue vers une URL dans le navigateur headless',
    '{"type": "object", "required": ["url"], "properties": {"url": {"type": "string", "format": "uri"}}}',
    'text'
),
(
    (SELECT id FROM mcp_servers WHERE name='playwright'),
    'browser_snapshot',
    'Capture l''état accessible de la page courante',
    '{"type": "object", "properties": {}}',
    'text'
);

-- ─── Resources ───────────────────────────────────────────────

INSERT OR IGNORE INTO resources (server_id, uri, name, description, mime_type, is_template) VALUES
(
    (SELECT id FROM mcp_servers WHERE name='jobspy'),
    'jobs://latest-summary',
    'Résumé dernière recherche',
    'Tableau Markdown des offres issues de la dernière recherche search_jobs',
    'text/markdown',
    0
),
(
    (SELECT id FROM mcp_servers WHERE name='jobspy'),
    'jobs://results/{search_term}',
    'Résultats par terme',
    'Offres filtrées pour un terme de recherche donné',
    'application/json',
    1
),
(
    (SELECT id FROM mcp_servers WHERE name='filesystem-pipeline'),
    'file://{path}',
    'Fichier local',
    'Accès en lecture à un fichier local par son chemin absolu',
    'text/plain',
    1
),
(
    (SELECT id FROM mcp_servers WHERE name='sequential-thinking'),
    'thinking://session/{session_id}',
    'Session de raisonnement',
    'Historique des étapes de pensée d''une session',
    'application/json',
    1
);

-- ─── Prompt Templates ────────────────────────────────────────

INSERT OR IGNORE INTO prompt_templates (server_id, name, title, role, template, variables, task_type, model_hint) VALUES
(
    (SELECT id FROM mcp_servers WHERE name='jobspy'),
    'cv_extraction',
    'Extraction structurée de CV',
    'user',
    'Extrais les informations suivantes de ce CV et retourne UNIQUEMENT un JSON valide.

Champs attendus :
- name (string)
- job_title (string) : métier principal / poste recherché
- skills (list[string]) : compétences techniques
- city (string | null) : ville actuelle
- experience_years (int | null) : années d''expérience estimées

CV :
{{cv_text}}

Réponds uniquement avec le JSON, sans texte autour.',
    '["cv_text"]',
    'extraction',
    'claude-haiku-4-5-20251001'
),
(
    (SELECT id FROM mcp_servers WHERE name='jobspy'),
    'job_matching_analysis',
    'Analyse de pertinence CV/Offre',
    'user',
    'Tu es un expert RH. Analyse la pertinence entre ce profil candidat et cette offre d''emploi.

PROFIL CANDIDAT :
{{cv_json}}

OFFRE D''EMPLOI :
{{job_description}}

Fournis :
1. Score de pertinence (0-100)
2. Points forts du candidat pour ce poste
3. Compétences manquantes
4. Recommandation finale (OUI / PEUT-ÊTRE / NON)

Format JSON.',
    '["cv_json", "job_description"]',
    'matching',
    'claude-sonnet-4-6'
),
(
    NULL,
    'job_classification',
    'Classification de domaine métier',
    'user',
    'Classifie cette description de poste dans l''une des catégories suivantes :
data engineering, software development, data science, devops, project management, marketing, finance, human resources, sales, design.

Description :
{{job_description}}

Retourne uniquement le label le plus probable.',
    '["job_description"]',
    'classification',
    'typeform/distilbert-base-uncased-mnli'
),
(
    NULL,
    'search_query_builder',
    'Construction requête de recherche',
    'system',
    'Tu es un agent de recrutement. À partir du profil candidat suivant, génère la meilleure requête de recherche pour JobSpy.

Profil :
- Métier : {{job_title}}
- Ville : {{city}}
- Compétences : {{skills}}

Retourne un JSON avec : {"search_term": "...", "location": "...", "job_type": "fulltime"}',
    '["job_title", "city", "skills"]',
    'search',
    'claude-haiku-4-5-20251001'
);
