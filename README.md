# Pipeline de Matching Job : JobSpy + Hugging Face

Ce projet automatise la recherche d'emploi en filtrant les offres par localisation réelle et en classifiant le domaine via l'IA.

## Architecture
- **Interface :** Claude Desktop / MCP
- **Moteur de recherche :** `jobspy-mcp-server` (LinkedIn, Indeed, Glassdoor)
- **Analyse NLP :** Modèle `tkuye/job-description-classifier` (Hugging Face API)
- **Parsing CV :** Extraction structurée PDF vers JSON.

## Configuration

### 1. Pré-requis
- Node.js installé (pour npx).
- Un compte Hugging Face (pour l'API Key).

### 2. Installation du MCP
Ajoutez ceci à votre `claude_desktop_config.json` :
```json
{
  "mcpServers": {
    "jobspy": {
      "command": "npx",
      "args": ["-y", "@borgius/jobspy-mcp-server"]
    }
  }
}
