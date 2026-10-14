# Plan d'implémentation

Objectif : livrer une solution simple, reproductible et expliquée dans l'enveloppe
de 4 à 6 heures indiquée par le sujet. Les durées ci-dessous sont indicatives,
hors attente d'accès, installation et latence API. Un lot actif à la fois.

| Lot | Périmètre | Critère de sortie | Estimation | État |
| --- | --- | --- | --- | --- |
| 0 | Lire le sujet, inspecter les entrées, préparer les cinq documents requis et le squelette | Contrats tracés, risques identifiés, sources intactes | 25 min | Terminé |
| 1 | Environnement, CLI, chargement strict, Unicode, dates, univers canonique, audit sans API | Tests des entrées et fuseaux passés ; commande d'audit sur les fichiers réels | 45 min | Terminé |
| 2 | Client du modèle imposé, prompt versionné, schéma, validation, cache, budget et métriques | Tests simulés hors réseau ; erreurs explicites ; petit essai réel borné si accès disponible | 70 min | Validé techniquement et essai réel réussi ; omissions documentées pour la revue |
| 3 | Composition contrôlée, agrégation, exports stables et manifeste de run | Tests mathématiques et intégration simulée passés ; aucune sortie finale partielle | 40 min | Terminé |
| 4 | Exécution complète, revue humaine, analyse d'erreurs et correction ciblée | 100 articles traités ; sorties validées ; appels, tokens et coût/article mesurés | 55 min | Exécution terminée ; échantillon humain de 10 désaccords prêt à annoter |
| 5 | Analyse des résultats, présentation et répétition de remise | Commande testée dans un environnement propre, livrables et limites relus | 35 min | Version livrée choisie par mesure : `output/run-v6-vote3/final/` (prompt v6 avec rôles, 3 passes + vote, exactitude estimée 0,933 sur `review/reference-v1`) ; présentation et dépôt Git à faire |

Total indicatif : 4 h 30. Garder une marge pour les anomalies et accès API.

## Lot 1 — première itération de code

1. Rendre Python et Git disponibles ; créer le venv, initialiser Git localement,
   contrôler les exclusions. Aucun remote ou push implicite.
2. Installer uniquement les dépendances retenues ; produire un verrou et relever
   les versions effectivement testées, dont les données de fuseau sur Windows.
3. Implémenter `python -m aie2609 --help` et un mode d'audit sans réseau.
4. Charger les deux formats avec erreurs contextualisées, préserver les sources,
   normaliser uniquement les copies et canonicaliser les classes.
5. Tester données invalides, doublons, U+200B, fuseaux et invariance à l'ordre.

Preuve attendue : commande, résumé d'audit réel et tests passés dans le journal.

## Lot 2 — extraction et classification

Traiter l'article entier avec le référentiel complet de noms et tickers canoniques
au départ. Éviter un préfiltre lexical qui pourrait perdre les marques et filiales.
Faire identifier les entreprises et leur implication par le modèle, avec une
preuve textuelle interne. Le code valide ensuite la structure et les contraintes.

Écrire des réponses simulées pour : modèle qui invente un ticker, label inconnu,
JSON cassé, doublons, preuves absentes, interruption réseau et dépassement de budget.
Préparer un petit ensemble de revue humaine couvrant plusieurs rôles d'entreprises.
Documenter les limites des liens marque/parent qui ne peuvent être certifiés par
le seul référentiel. Aucun benchmark de précision inventé sans annotations.

Prérequis du test réel : clé disponible localement, accès à `gpt-5.6-terra`, tarif
vérifié et budget choisi. Ne pas changer de modèle pour contourner un accès manquant.

État du 12 octobre : commande `classify`, prévisualisation, cache validé, rapports
durables et tests simulés disponibles. Tarifs et contrat Responses vérifiés dans
la documentation officielle. Budget utilisateur reçu : 5 USD maximum pour le
premier essai, reprises comprises. Clé absente du processus et des variables
Windows utilisateur/machine inspectées : aucun appel réel. Le [jeu de revue](docs/REVIEW_SET.md)
est sélectionné, sans annotations de référence ni mesure de précision.

Complément du 13 octobre : à la demande de l'utilisateur, chargement automatique
de la clé depuis un `.env` local ignoré par Git, sans nouvelle dépendance. Modèle
et budget inchangés ; les tests de configuration et la suite hors réseau passent.
L'utilisateur peut maintenant renseigner la clé directement dans ce fichier.

Essai du 13 octobre exécuté : accès confirmé, trois articles traités par variante.
Version retenue `entity-sentiment-v2`, résultat `output/pilot-003`. Goldman Sachs
est récupéré dans N002 ; Alphabet via Waymo manque encore dans N027. Une variante
v3 avec rattachement plus explicite et raisonnement medium n'a pas amélioré le
résultat ; retour à v2, sans retouche des sorties. Avant le lot 4 : consolider la
détection des marques et mentions secondaires sur un échantillon distinct.
Coût connu cumulé 0,2368426 USD ; réservation inconnue 0,173757 USD ; solde prudent
4,5894004 USD. Voir le journal pour le détail de chaque tentative.

Refonte demandée ensuite par l'utilisateur : prompt v4 RCORCF, dix exemples
fictifs et documentation des versions. Validation hors réseau uniquement :
62 tests passent ; aucune nouvelle dépense. Le résultat v2 reste le point de
comparaison API, sans prétendre mesurer v4. Avant extension, évaluer v4 sur les
régressions connues et un échantillon distinct des cas enseignés dans le prompt.

Retest RCORCF demandé et exécuté : `output/pilot-005`, trois réponses validées,
neuf paires article/ticker. GS reste neutre et GOOGL via Waymo est maintenant
présent en neutre ; aucune autre variation de label ou de couverture par rapport
à v2. Coût du retest 0,0888659 USD ; solde prudent actualisé 4,5005345 USD.
Il s'agit de cas de développement connus, pas d'une mesure indépendante de qualité.

Test suivant demandé : dix articles distincts, attentes consignées avant les
appels dans `docs/REVIEW_10.md`. Run terminé après une reprise technique :
28 paires, omissions JPM/N070 et NWSA/N077, désaccord NFLX/N077. Le prompt v4 est
resté figé. Coût du test 0,2791525 USD ; 63 tests passent après ajout du motif de
validation aux diagnostics. À résoudre en revue avant généralisation.

Extension demandée et exécutée : contrôle lexical consultatif et commande
`review`, prompt de relecture `entity-review-v1`. Les 71 tests hors réseau passent.
Run `output/verification-010` : dix appels, 0,2744812 USD ; ajout de NWSA/N077,
suppression régressive de P/N084, JPM/N070 toujours absent. Les deux résultats
restent séparés : aucun gain net démontré et pas de promotion automatique.
La suppression de P est signalée par le contrôle lexical. Prochain travail de
qualité : arbitrage humain des cas consignés dans `docs/REVIEW_10.md`, puis une
correction ciblée avec contrôle des régressions. Le jeu de référence humain
reste à valider ; la relecture par le même modèle ne le remplace pas.

Correction ciblée suivante terminée : registre `entity-aliases-v1`, couverture
`entity-coverage-v2` et prompt `entity-review-v2-targeted`. La commande sélectionne
les omissions fiables et mentions ambiguës par défaut, avec `--all` pour le mode
général. Sur N070/N077/N084 : JPM et NWSA ajoutés, P conservé, aucun NDAQ ; NFLX
reste negative. Trois appels, 0,0927612 USD. Les 74 tests passent. Le mécanisme
améliore la couverture de cet échantillon à coût réduit, sans constituer une mesure
généralisable ni une validation humaine indépendante. La proposition n'est pas
fusionnée automatiquement avant le calcul.

Test complet demandé ensuite : 100 articles terminés dans `output/full-100-v4`,
87 appels et 13 caches, coût 2,2450432 USD. L'analyse initiale des alertes a révélé
37 faux signaux dus à des mots communs ou acronymes ; `entity-coverage-v3` et
`entity-aliases-v2` les éliminent et laissent huit cas plausibles. Leur relecture
coûte 0,2281222 USD et ajoute huit paires neutres sans suppression ou changement
de label. Les 75 tests passent. Composition finale à implémenter explicitement au
lot 3 avant les CSV ; pas de fusion manuelle des artefacts.

Avant la composition, le prompt v5 ajoute une règle et deux exemples synthétiques
pour les comparaisons de marché incidentes et les accords asymétriques ; le registre
v3 ajoute CNN → WBD. Les tests hors réseau passent. La passe complète v5 produit
220 paires et corrige les cas visés, mais introduit des omissions et deux faux XYZ.
Le lot 3 doit donc composer des propositions validées et conserver les alertes,
sans promouvoir automatiquement la dernière passe.

Composition déterministe maintenant implémentée avec provenance, empreintes,
validation des revues et comparaison facultative d'une candidate. Le registre
`entity-aliases-v5` ajoute CNBC, CBS News, Barron's et Kenworth, et interdit les
associations `X → XYZ` et `SpaceX → XOM`. Sur les 100 articles, la composition
v4 + huit revues contient 225 paires mais reste bloquée par sept alertes ; v5
compte quinze alertes bloquantes et 29 désaccords. Le scoring ne démarre pas tant
que ces cas n'ont pas une décision reproductible.

Les six articles concernés ont ensuite été relus par groupes bornés. Le mode
`additions-only` refuse au validateur toute suppression ou modification de label ;
il a empêché la suppression régressive de SCHW/N066. La composition finale v2
contient 230 paires, zéro blocage et `ready_for_scoring=true`. Les seuls écarts
avec les 225 paires précédentes sont six ajouts neutres (CMCSA quatre fois, PSKY
et NWSA) et le retrait du faux XOM/N100. Le calcul peut partir de ce fichier.

Calcul et export terminés avec `time-decay-v1`. La commande `export` refuse un
rapport non approuvé ou une empreinte de classifications différente, calcule les
durées en UTC depuis la référence fixe, utilise `math.fsum` puis écrit les deux
CSV et leur manifeste. `output/final-results-v1/` contient 230 entités et 111
tickers. Les tests couvrent 0/7/14 jours, fraction de jour, changement d'heure,
annulation, score neutre nul, date future, tri, empreintes et contrat CSV.

## Lot 3 — calcul et contrat de sortie

Tester les poids à 0, 7 et 14 jours, une fraction de jour et un passage d'heure
saisonnière. Vérifier score négatif, annulation, entreprise uniquement neutre et
une ligne par paire canonique. Trier les exports. Le run réussit seulement lorsque
chaque article a un résultat validé, y compris une liste vide justifiée.

## Lots 4 et 5 — résultat et remise

- Lancer un petit essai pour mesurer le coût avant d'étendre aux 100 articles.
- Réutiliser le cache valide ; séparer coût du run avec cache et coût d'un run complet.
- Examiner notamment banques analystes, filiales, classes multiples, noms ambigus
  et textes avec caractères invisibles. Conserver le jeu de revue et ses limites.
- Expliquer les tickers saillants avec leurs articles et contributions pondérées,
  la concentration de couverture et les limites de confiance.
- Toute correction déclenche une régénération ; ne pas retoucher les CSV.
- Faire une répétition de la commande complète dans un environnement propre.
- Vérifier confidentialité, absence de secrets et présence de chaque livrable.

## Décisions et points à résoudre

| Point | Position actuelle | Moment de résolution |
| --- | --- | --- |
| Python / Git absents du terminal | Runtimes locaux vérifiés dans les dossiers ignorés `.tools`; `.venv` reproductible | Résolu au lot 1 |
| Accès et tarif du modèle imposé | Tarifs vérifiés le 12 octobre ; accès Responses confirmé le 13 octobre | Résolu au lot 2 |
| Budget utilisateur | 100 USD autorisés le 14 octobre ; 14,1736621 USD connus + 0,529338 USD réservés pour tentatives inconnues ; engagement prudent 14,7030001 USD | Suivi dans les rapports et le journal |
| Fuseau et échéance « CET » | Entrées New York certaines ; ambiguïté de remise à clarifier | Avant remise |
| Filiales non décrites par le CSV | Inférence modèle traçable + revue ; pas de source externe | Lot 2 / revue lot 4 |
| Stabilité du modèle | Cache et contrats stables ; pas de promesse de déterminisme de l'API | Lots 2 et 4 |
