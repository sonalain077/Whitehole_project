# Stratégie de tests

La suite `unittest` couvre actuellement l'ingestion, la normalisation ciblée,
les dates New York, les doubles classes et l'audit des fichiers fournis, ainsi que
la classification avec un client simulé, le transport simulé, le cache et le budget.
Elle ne fait aucun appel réseau. Ajouter les tests des lots suivants avec leur comportement.

| Lot | Comportements à couvrir |
| --- | --- |
| 1 | JSON/CSV invalides, clés et identifiants dupliqués, champs manquants, U+200B, classes canoniques, dates invalides/ambiguës/inexistantes, article futur — implémenté |
| 2 | Schéma modèle, ticker hors univers, labels, preuves, doublons, refus/incomplétude, reprises bornées, cache, budget, métriques avant envoi, erreurs réseau masquées, CLI sans dépense — implémenté |
| 3 | Poids 0/7/14 jours, fraction de jour, passage DST, signes, neutralité, somme stable, colonnes et ordre exacts, entrées préservées, échec sans faux succès |
| 4 | Intégration hors réseau avec client simulé, permutation des entrées, répétition depuis le cache, revue sémantique manuelle distincte |
| 5 | Commande `run` : run sans relecture, omission corrigée en `additions-only`, relecture rejetée avec export marqué en alerte, dossier existant refusé — implémenté (`test_pipeline.py`) |

Commande :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Une commande qui découvre zéro test ne valide pas la pipeline. Les futurs tests
d'intégration API devront être explicitement activés et soumis au budget utilisateur.
