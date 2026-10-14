# Inspection initiale des données

Inspection en lecture seule le 12 octobre 2026 avec PowerShell et Node, sans API.
L'audit Python du lot 1 confirme les comptages, la plage des dates, les classes
canoniques et les deux anomalies U+200B sur les fichiers fournis.

| Contrôle | Résultat observé |
| --- | --- |
| Articles | 100 |
| Champs présents | `id`, `date`, `headline`, `body` |
| Identifiants dupliqués | Aucun |
| Champs requis vides ou non textuels | Aucun dans le contrôle initial |
| Format textuel des dates | 100 conformes à `YYYY-MM-DDTHH:MM` |
| Plage des dates | 2026-08-25T06:53 à 2026-09-28T16:20 |
| Lignes du référentiel | 503 |
| Symboles dupliqués | Aucun |
| Secteurs distincts | 11 |
| Contenus identiques après normalisation exploratoire | Aucun |
| Caractère de remplacement U+FFFD | Aucun trouvé dans les articles |
| Caractères invisibles U+200B | Détectés dans `N027` et `N100` |

Dans `N027` et `N100`, U+200B coupe le nom Tesla et/ou le ticker TSLA. Un simple
matching brut peut donc manquer ces entités. Prévoir un nettoyage ciblé en mémoire,
un signalement dans l'audit et des tests de non-régression. L'exploration a aussi
comparé les corps après retrait des caractères U+200B à U+200F et U+FEFF pour
chercher des doublons ; ce nettoyage large n'est pas la politique retenue en production.

Le référentiel contient `GOOGL/GOOG`, `FOXA/FOX`, `NWSA/NWS` et `BRK.B`. Les 503
lignes ne doivent pas être ramenées arbitrairement à 500 ; appliquer les règles
de classes du sujet au moment de construire l'univers canonique.

Contrôles restant à automatiser : parsing strict incluant les clés dupliquées,
validité calendaire et fuseaux, anomalies du référentiel, caractères confondables,
champs supplémentaires, sorties du modèle et invariance sur entrées équivalentes.
Aucune conclusion sur la qualité sémantique des articles ou les sentiments à ce stade.

## Empreintes SHA-256 des sources

```text
AIE2609_Project.pdf
8bafe85dc0e06eaf59f4be17d45fc6c6d126b3f5f49818522f03a541bb157195

news.json
2bd735fcee63c39d6a41c7a07764bd09b9199d3eeedda951b2546fb94ebc6354

sp500.csv
ce3136f433a6bd493a0c5b7a4d1e18e40f58f5fdf13bf989402cc6e0bffb7b7c
```

Ces empreintes permettent de vérifier que les entrées n'ont pas changé.
