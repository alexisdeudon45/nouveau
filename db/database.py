"""Couche d'accès à la base de données SQLite — Méthode Cerise Modulaire."""
import json
import sqlite3
from pathlib import Path

DB_PATH   = Path(__file__).parent / "registry.db"
SCHEMA    = Path(__file__).parent / "schema.sql"
SEED      = Path(__file__).parent / "seed.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(force: bool = False) -> None:
    if force and DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()
    conn.executescript(SCHEMA.read_text())
    conn.executescript(SEED.read_text())
    conn.commit()
    conn.close()
    print(f"Base initialisée → {DB_PATH}")


# ── MCP Servers ───────────────────────────────────────────────

def get_all_servers() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM mcp_servers WHERE is_active=1 ORDER BY name")]


def get_server(name: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM mcp_servers WHERE name=?", (name,)).fetchone()
        return dict(row) if row else None


def register_server(name: str, description: str, transport: str = "stdio",
                    command: str = None, args: list = None, env_vars: dict = None,
                    version: str = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT OR REPLACE INTO mcp_servers
               (name, description, transport, command, args, env_vars, version)
               VALUES (?,?,?,?,?,?,?)""",
            (name, description, transport, command,
             json.dumps(args or []), json.dumps(env_vars or {}), version)
        )
        conn.commit()
        return cur.lastrowid


# ── Tools ─────────────────────────────────────────────────────

def get_tools(server_name: str) -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT t.* FROM tools t
               JOIN mcp_servers s ON t.server_id=s.id
               WHERE s.name=? AND t.is_active=1""",
            (server_name,)
        )]


def get_tool(server_name: str, tool_name: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """SELECT t.* FROM tools t
               JOIN mcp_servers s ON t.server_id=s.id
               WHERE s.name=? AND t.name=?""",
            (server_name, tool_name)
        ).fetchone()
        return dict(row) if row else None


# ── Resources ─────────────────────────────────────────────────

def get_resources(server_name: str) -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT r.* FROM resources r
               JOIN mcp_servers s ON r.server_id=s.id
               WHERE s.name=?""",
            (server_name,)
        )]


# ── Prompt Templates ──────────────────────────────────────────

def get_prompt(name: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM prompt_templates WHERE name=?", (name,)
        ).fetchone()
        return dict(row) if row else None


def render_prompt(name: str, **kwargs) -> str:
    prompt = get_prompt(name)
    if not prompt:
        raise ValueError(f"Prompt '{name}' introuvable en base.")
    template = prompt["template"]
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def get_prompts_by_task(task_type: str) -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM prompt_templates WHERE task_type=?", (task_type,)
        )]


# ── Utilitaire CLI ────────────────────────────────────────────

def print_registry() -> None:
    servers = get_all_servers()
    print(f"\n{'='*60}")
    print(f"  REGISTRE MCP — {len(servers)} serveur(s) actif(s)")
    print(f"{'='*60}")
    for s in servers:
        tools = get_tools(s["name"])
        resources = get_resources(s["name"])
        print(f"\n🍒 {s['name']} (v{s['version']}) [{s['transport']}]")
        print(f"   {s['description']}")
        print(f"   Tools     : {', '.join(t['name'] for t in tools) or 'aucun'}")
        print(f"   Resources : {', '.join(r['uri'] for r in resources) or 'aucune'}")
    print()


if __name__ == "__main__":
    init_db()
    print_registry()
