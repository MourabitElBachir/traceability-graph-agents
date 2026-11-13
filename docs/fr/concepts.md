# Concepts

Une **ontologie** est un vocabulaire partagé : types d’objets, relations et règles. Ce n’est pas un logiciel. OWL est le langage, RDF le modèle de triplets, Turtle une syntaxe, Protégé un éditeur. Ici le fichier est `ontology/traceability.ttl`.

Le **graphe de connaissances** est ce vocabulaire rempli de faits. Le **graphe de propriétés** (Neo4j) range ces faits en nœuds et relations, ce qui convient à « qu’est-ce qui est en aval de `BLE-0457` ? ».

**EPCIS** (GS1) décrit des événements : quoi, quand, où, pourquoi. Le dépôt s’en inspire. Il n’implémente pas EPCIS et n’utilise pas de vraies clés GS1.

Le **RAG** classique cherche des textes proches. Il répond mal à une question de chaîne. Le **GraphRAG** de ce dépôt parcourt le graphe pour `BLE-0457 → FAR-118 → BIS-031` et n’utilise les vecteurs que pour les comptes rendus (audit, certificat).

**LangChain** sert aux modèles de prompt. **LangGraph** exécute le flux : routeur, agents, checkpointer, interruption avant d’émettre un rappel.

**MCP** publie `trace_lot`, `check_certificates`, `search_documents`. **A2A** est ici une carte et un endpoint de tâche, clairement marqués comme sous-ensemble (`a2a-minimal-0.1`).

Exemple : le blé `BLE-0457` est moulu en `FAR-118` puis en biscuits `BIS-031`, sous le certificat valide `CERT-77`.
