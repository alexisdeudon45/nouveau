# Nouveau — Conception du pipeline optimal

## Contenu

- **`agent.md`** — prompt à donner à Claude pour qu'il conçoive le pipeline optimal

## Comment utiliser

1. Ouvre `agent.md`
2. Copie l'intégralité du contenu
3. Colle-le dans une conversation Claude (claude.ai ou Claude Code)
4. Claude te répondra avec :
   - Le pipeline recommandé étape par étape
   - Les inputs et outputs de chaque étape
   - Les KPIs pour mesurer la qualité des résultats
   - L'architecture adaptée à Home Assistant OS

## Contexte

Ce prompt fait suite au développement de HA-MCP — un orchestrateur de serveurs MCP qui tourne dans Home Assistant. L'objectif est de concevoir le meilleur pipeline possible pour analyser automatiquement des candidatures (offre d'emploi + CV) en utilisant Claude et des outils externes.

Le pipeline actuel comporte 14 étapes. Ce prompt demande à Claude de proposer une architecture optimale en partant des contraintes réelles du système.
