# AgriTrace — résumé

[Texte canonique en anglais](../../README.md). Données **fictives**. Aucune entreprise cliente.

## Le problème

Une équipe qualité doit savoir d’où vient un lot, où il est allé, et si son certificat est encore valable. Un rappel ne part pas tout seul : une personne valide la recommandation.

## La chaîne de référence

```text
blé BLE-0457 → farine FAR-118 → biscuits BIS-031
certificat CERT-77 (Organic Horizon, fictif, valide jusqu’au 2027-12-31)
```

Ferme des Collines récolte le blé. Le Moulin du Val produit la farine. Le Fournil Lumière cuit les biscuits. DistriNord les livre à l’Épicerie Rive. L’horloge du démonstrateur est le 2026-11-13.

D’autres lots existent pour les anomalies, pas pour l’exemple principal : `CERT-78` périmé, farine mélangée `FAR-221`, huile `OIL-009` sans lot source.

## Ce que le dépôt montre

- Une ontologie OWL (Turtle), inspirée des questions EPCIS quoi / quand / où / pourquoi, sans clés GS1 réelles.
- Un extrait SQL (le ERP) puis un graphe.
- Une recherche hybride : parcours de graphe + chunks vectorisés.
- Des agents LangGraph (supervision, traçabilité, conformité, documents) avec interruption avant le rappel.
- Trois outils MCP et une carte A2A minimale (`a2a-minimal-0.1`).
- Un mode `LLM_MODE=mock` pour les tests et la CI, sans clé d’API.

## Démarrage

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec app python -m agritrace.demo
```

Sans Docker : `uv venv --python 3.11`, installation du paquet, `make demo`.

## Pages

- [Concepts](concepts.md)
- [Architecture](architecture.md)
- [Outils](outils.md)
- [Sécurité et gouvernance](securite-gouvernance.md)
- [Architecture cible](architecture-cible.md)
