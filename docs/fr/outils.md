# Outils

| Outil | Rôle dans ce dépôt |
| --- | --- |
| Neo4j, Cypher, index vectoriel | Graphe questionnable, contraintes, similarité des chunks |
| OWL, Turtle, rdflib | Vocabulaire versionné `0.1.0` |
| Idées EPCIS | Quoi, quand, où, pourquoi, sans clés GS1 |
| SQLite (schéma proche de Postgres) | ERP source. Postgres n’est pas branché |
| Python 3.11, Pydantic | Lots et certificats typés |
| LangChain | Prompts Cypher et narration |
| LangGraph | Supervision, checkpoint, interruption |
| SDK MCP | `trace_lot`, `check_certificates`, `search_documents` |
| A2A minimal | Carte `a2a-minimal-0.1` et `POST /a2a/tasks` |
| FastAPI | `/ask`, reprise, Cypher en lecture seule |
| Streamlit | Même service, avec acteur et boutons d’approbation |
| OpenTelemetry | Spans. Export désactivé par défaut |
| LangSmith | Optionnel, via variables d’environnement |
| LLM compatible OpenAI / mock | Mock par défaut, aucune clé en CI |
| Docker Compose | Neo4j 5.26 et l’API |
| pytest, GitHub Actions | Chaîne `BLE-0457` / `FAR-118` / `BIS-031` / `CERT-77` |
| uv, ruff, mypy | Environnement, style, types |
| Mermaid | Schémas du README. SVG/PNG dans `docs/assets` |

Le détail anglais, avec extraits de code, est dans [docs/tools.md](../tools.md) et dans le README.
