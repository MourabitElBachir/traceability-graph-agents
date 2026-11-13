# Sécurité et gouvernance

**Lignage.** Les nœuds viennent de l’extrait SQL (`source_system=erp-sqlite`) et portent `ontology_version`.

**Catalogue et version.** `ontology/traceability.ttl` est le catalogue (`owl:versionInfo 0.1.0`). `GET /ontology` le résume.

**Qualité.** Une référence cassée empêche le chargement. Un certificat périmé (`CERT-78`) ou une transformation sans lot source (`OIL-009`) est un *constat*, pas une erreur de chargement.

**Accès par acteur.** Un détaillant voit les lots qui lui sont livrés et leur amont. L’Épicerie Rive voit `BIS-031` et donc `FAR-118` et `BLE-0457`. Elle ne voit pas `OIL-009`. Le producteur voit l’aval de sa récolte. Seul le rôle régulateur approuve un rappel. Le Cypher libre est réservé à l’auditeur et au régulateur.

**Secrets.** Pas de clé dans le dépôt. Le mot de passe Neo4j de Compose est un repli local, documenté comme tel.

**Données personnelles.** Aucune personne réelle. Le journal de démo peut contenir la question ; en production il faudrait la réduire et fixer une durée de conservation. Le mode mock n’envoie rien à un fournisseur.

**Garde-fous modèle.** Détection d’injonctions du type « ignore les instructions ». Cypher en lecture seule, labels autorisés, `LIMIT` plafonné. Les réponses citent des identifiants issus des outils.

**Humain, passerelle, suivi.** Le rappel reste `needs_approval`. La passerelle LLM est `LLM_MODE` et une URL compatible OpenAI. OpenTelemetry est optionnel.

**AI Act.** Un rappel qui retire un aliment du rayon exige une personne. Ce dépôt est une démo, pas une évaluation de conformité. Ces lignes sont des choix d’ingénierie, pas un avis juridique.
