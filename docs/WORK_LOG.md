# Journal de travail

## 2026-10-12 — itération 0

**Demande :** planifier et initialiser le projet en commençant par un contexte agent
méthodique, puis travailler de façon itérative et sûre.

**Réalisé :** lecture textuelle des cinq pages du sujet via les tables de caractères
du PDF ; inspection des entrées ; création des cinq documents imposés, du présent
journal, du constat de qualité, des exclusions et du squelette Python minimal.
Le PDF n'a pas été modifié. Pas de contrôle de rendu visuel du PDF source.

**Choix :** pipeline Python locale ; version cible initiale 3.12 ; code pour les
contrats et calculs, modèle imposé pour la compréhension ; cache et budget dès le
premier client API. Pas de framework applicatif, de dépendances métier prématurées
ou de logique factice présentée comme une implémentation.

**Vérifications exécutées :** inventaire des fichiers ; parsing JSON avec Node ;
CSV avec `Import-Csv` ; recherche de champs vides, doublons et caractères invisibles ;
empreintes via `Get-FileHash -Algorithm SHA256`. Résultats dans `DATA_QUALITY.md`.
Le décompte JSON a été vérifié sous Node (100) après constat qu'une enveloppe de
tableau PowerShell comptait incorrectement le tableau entier comme un seul élément.

**Relecture finale :** 12 fichiers créés contrôlés ; liens Markdown locaux résolus,
fins de fichier présentes et absence de caractères de remplacement. Les trois
empreintes SHA-256 recalculées correspondent aux sources initiales. Contrôles
documentaires et d'intégrité réussis ; ils ne remplacent pas les tests Python.

**Limites :** `git`, `python`, `py`, `uv` et `pdftotext` non accessibles dans le
terminal inspecté. Aucun venv, dépôt Git, verrou de dépendances, test Python ou run
de classification créé/exécuté. Aucun appel API ni coût de classification engagé.

**Suite :** lot 1 du plan : outillage, ingestion, normalisation et audit sans réseau.

## 2026-10-12 — itération 1

**Objectif :** fournir une CLI d'audit hors réseau, valider strictement les deux
entrées, normaliser sans modifier les sources, gérer le fuseau New York et produire
un univers canonique testable.

**Réalisé :** modules `errors`, `models`, `normalization`, `dates`, `ingestion`,
`audit`, `cli` et point d'entrée `python -m aie2609`. La commande `audit` propose
une sortie humaine ou JSON. Les clés JSON, colonnes CSV, champs, types, doublons,
dates ambiguës/inexistantes, articles futurs et classes d'actions sont validés.
Les textes bruts et normalisés restent distincts en mémoire.

**Environnement :** Python 3.12.10 officiel installé localement dans `.tools`,
signature Authenticode valide (Python Software Foundation) et MD5 conforme à la
page de publication. `tzdata==2026.5` et `setuptools==82.0.1` sont verrouillés avec
leurs SHA-256. Environnement `.venv` créé et package installé en mode éditable.
MinGit 2.56.0.windows.2 officiel, SHA-256 vérifié, installé dans `.tools`; dépôt
local initialisé sur `main`, sans commit et sans remote. Les outils locaux, le venv
et les téléchargements sont ignorés par Git.

**Vérifications :** compilation Python réussie et `pip check` sans dépendance
cassée. Après un premier échec attendu dû à l'absence de base IANA sous
Windows, ajout de `tzdata`; les 15 tests initiaux passent ensuite. L'audit réel
retourne 100 articles, 503 lignes source, 500 sociétés canoniques, dates du
2026-08-25T06:53 au 2026-09-28T16:20 et deux anomalies non bloquantes : 6 U+200B
dans `N027`, 10 dans `N100`. La relecture finale confirme les 16 tests, dont le
code de sortie d'une erreur CLI, ainsi que les empreintes originales des trois
sources. Aucun appel API.

**Limites :** la CLI ne classifie encore aucun article et ne génère pas les CSV.
Le sandbox d'exécution a un autre propriétaire Windows que le dossier : les commandes
Git de l'agent utilisent ponctuellement `-c safe.directory=...`; cela ne modifie pas
la configuration globale et ne devrait pas concerner le compte propriétaire.

**Suite :** lot 2, client du modèle imposé, prompt, validation stricte, cache,
budget et métriques avec tests simulés avant tout appel réel.

## 2026-10-12 — itération 2, validation hors réseau

**Demande :** commencer l'extraction et la classification avec la clé du modèle
fournie pour le projet. La clé ne doit pas être partagée dans la conversation.

**Réalisé :** commande `classify` avec sélection par identifiants ou limite,
prévisualisation sans réseau, prompt `entity-sentiment-v1`, JSON Schema strict,
validation des tickers, labels, doublons et extraits exacts. Ajout du transport
Responses standard, cache par empreinte de la requête, budget en Decimal et
rapports durables avant chaque appel. Le résultat interne contient une analyse
distincte par article et entreprise. Les CSV et le score restent au lot 3.

**Choix :** bibliothèque standard `urllib` sans nouveau SDK ; endpoint OpenAI
fixe, redirections refusées, aucune substitution de modèle, clé uniquement via
environnement. Reprises bornées pour réponse invalide ou limitation de débit
identifiée ; une réponse réseau perdue n'est pas automatiquement redemandée.
Un coût inconnu reste explicite et sa réservation est conservée. Cache local et
cache fournisseur sont comptabilisés séparément. Le plafond local est estimatif.

**Prompt initial :** rôle propre de chaque entreprise, mentions incidentes
neutres, rattachement de marques/filiales, distinction partenaire/investisseur
versus parent, noms Unicode ressemblants confirmés par le contexte. L'extrait
doit conserver la graphie du texte normalisé. Aucune retouche des entrées.
Le jeu `REVIEW_SET.md` propose huit articles à annoter ; il n'est pas une référence
humaine déjà validée et aucun score de qualité sémantique n'est annoncé.

**Documentation API vérifiée :** fiche officielle `gpt-5.6-terra`, Responses,
Structured Outputs et catégories de cache. Tarifs datés et liens consignés dans
`ARCHITECTURE.md` et le code de consommation. Le contrat réel de la clé et sa
compatibilité avec les champs attendus devront être confirmés au petit essai.

**Vérifications exécutées :**

- `python -m unittest discover -s tests -v` via le venv : 54 tests passent, sans
  réseau. Cas couverts : validation, cache rejoué et corrompu, dépassement de
  budget, retries comptabilisés, consommation absente, réponse tronquée, timeout,
  refus/incomplétude, absence de redirection et prévisualisation CLI sans client.
- `python -m pip check` : aucune dépendance cassée ; `compileall -q src tests`
  réussi. Aucune dépendance supplémentaire installée au lot 2.
- `python -m aie2609 audit` : 100 articles, 503 lignes et 500 sociétés canoniques,
  mêmes deux anomalies U+200B que le lot 1.
- `classify --ids N001 N002 N027 --dry-run` : trois requêtes préparées sans appel
  ni artefact, réservation cumulée des premières tentatives de 0,5156135 USD.
  Ce montant est une estimation prudente, pas un coût mesuré ni garanti.
- Empreintes SHA-256 des trois sources inchangées ; liens Markdown locaux et
  encodage contrôlés ; aucun motif de clé API trouvé dans le code et les documents.
  État Git relu, aucun commit ou push réalisé.

**Limites et suite :** aucun appel API ni coût engagé. `OPENAI_API_KEY` est absente
du processus inspecté ; budget demandé, sans réponse reçue à cette étape. Le lot 2
est implémenté et validé techniquement hors réseau, mais l'essai réel et la revue
des prédictions restent à faire après configuration locale et budget explicite.
Prochain essai proposé : N001, N002, N027, une tentative chacun, puis inspection
des analyses et coûts avant extension.

## 2026-10-12 — budget du premier essai confirmé

L'utilisateur autorise « max 5 usd » pour le premier essai. Plafond cumulé de
5 USD, reprises comprises ; cette autorisation persiste et ne doit pas être
redemandée. Commencer par N001, N002 et N027, une tentative chacun, puis examiner
les résultats avant toute extension. Ne pas réinitialiser ce plafond en créant
un nouveau dossier de run après une erreur.

Vérification limitée à la présence de `OPENAI_API_KEY`, sans affichage de valeur :
absente du processus, des variables utilisateur Windows et des variables machine.
Aucun appel API exécuté, aucune dépense. Il reste à configurer la clé localement
dans l'environnement qui exécutera la commande. Aucun code changé à cette étape.

## 2026-10-13 — configuration locale simplifiée

**Demande :** utiliser `.env` pour éviter les commandes PowerShell de saisie.

**Réalisé :** ajout de `config.py`, chargé uniquement par `classify` après
validation des arguments et du budget, avant construction du client. Lecture de
la seule clé `OPENAI_API_KEY` dans le dossier courant ; environnement non vide
prioritaire, aucune exécution/interpolation, erreurs sans contenu secret. Un
fichier `.env` vide a été créé en mode exclusif pour ne jamais écraser un fichier
existant ; `.env.example` reste sans clé. L'exclusion `.env` existait déjà.

**Vérifications :** 60 tests passent avec `unittest discover -s tests -q`, sans
réseau. Tests de formats simples et guillemets, BOM, priorité de l'environnement,
fichier absent/vide, doublons, encodage invalide, absence de fuite dans les erreurs
et absence de chargement en prévisualisation. Aucun appel API effectué.

**Suite :** renseigner la clé localement et enregistrer `.env`, puis lancer le
petit essai déjà autorisé dans le budget cumulé de 5 USD.

## 2026-10-13 — premier pilote API et revue des omissions

**Autorisation :** clé enregistrée par l'utilisateur dans `.env`, puis confirmation
« c'est enregistre ». Budget cumulé de 5 USD déjà autorisé. Aucune valeur de clé
affichée ou copiée dans les rapports ; présence seule vérifiée.

**Exécution :** N001, N002 et N027, une tentative par article et par variante,
modèle imposé `gpt-5.6-terra`. Premier lancement bloqué par le réseau du sandbox ;
diagnostic sans authentification : `PermissionError / WinError 10013`. Relance
avec accès réseau approuvé, dans un nouveau dossier et avec budget diminué de
la réservation initiale, conservée par prudence. Aucun changement d'endpoint.

| Dossier | Version | Résultat | Coût connu USD | Réservation inconnue USD |
| --- | --- | --- | --- | --- |
| output/pilot-001 | v1 | Échec réseau au premier article | 0 | 0,173757 |
| output/pilot-002 | v1 | 3 articles, 3 réponses validées | 0,0789105 | 0 |
| output/pilot-003 | v2 | 3 articles, 3 réponses validées ; résultat retenu | 0,0787458 | 0 |
| output/pilot-004 | v3 expérimentale | 3 articles, 3 réponses validées ; non retenue | 0,0791863 | 0 |

Les trois runs aboutis rapportent 98 835 tokens d'entrée et 1 470 tokens de sortie
au total (catégories de cache détaillées dans leurs `usage.json`). Neuf réponses
reçues et une tentative locale échouée. Coût connu cumulé : **0,2368426 USD** ;
coût de la tentative réseau inconnu dans le rapport. Engagement conservateur :
**0,4105996 USD**, solde du budget initial : **4,5894004 USD**. Aucun coût inconnu
n'a été remplacé par zéro et aucun budget n'a été renouvelé entre les variantes.

**Revue assistée :** lecture des trois articles, contrôle du référentiel et
comparaison des résultats. La version v1 omet GS dans N002 et GOOGL via Waymo
dans N027. La v2 impose un inventaire par paragraphe, avec banques analystes,
sources et comparaisons, avant sentiment ; GS est récupéré. La v3 clarifie les
liens de filiation connus et passe le raisonnement de low à medium ; elle omet
encore GS et GOOGL. Retour au prompt v2 et au raisonnement low, sans retoucher
les résultats. L'effet propre de chacun des deux changements de v3 n'est pas
isolé par cet essai. Le cas Waymo reste une limite à résoudre, pas un succès.
La table de revue est dans `REVIEW_SET.md`, sans prétention de validation humaine
indépendante ou de précision mesurée sur un échantillon représentatif.

**Vérifications finales :** 60 tests hors réseau passent après retour à v2.
Les empreintes de requêtes actuelles correspondent exactement à `pilot-003` ;
ses réponses repassent le validateur, les empreintes des deux entrées restent
identiques à celles du manifeste. Git ignore `.env`, les sorties et le cache.
Pas de commit, push, exposition de secret ou retouche des sources.

**État :** intégration API validée sur un petit essai ; rappel sémantique encore
insuffisant sur une mention de filiale. Le prochain lot de code reste calcul et
exports ; avant le run des 100 articles, fiabiliser le rappel et vérifier sur des
articles distincts de ceux utilisés pour ajuster le prompt. Ne pas traiter les
100 articles sur la seule base de la validation structurelle du pilote.

## 2026-10-13 — refonte du prompt selon RCORCF

**Demande :** soigner le prompt système selon Rôle, Contexte, Objectif, Résultat,
Contraintes, Format, avec des exemples détaillés, et expliquer les deux versions.

**Réalisé :** réécriture de `SYSTEM_PROMPT` en six sections dans
`classification.py`, consignes en anglais et titres bilingues. Ajout de dix
exemples synthétiques avec univers propre, article, objet JSON complet et note
pédagogique. Règles détaillées pour neutralité, filiales, sources, classes,
incertitude d'identité, nouvelles mixtes, temporalité, Unicode, preuves exactes
et instructions malveillantes dans les données. Modèle, schéma, effort low et
traitement des entrées inchangés.

**Versions :** `entity-sentiment-v4-rcorcf` actif pour les prochains appels ; v3
avait déjà servi à un essai, son numéro n'est pas recyclé. Normalisation conservée
à `nfc-lf-u200b-v1`, puisque sa politique n'a pas changé. Le pilote v2 reste un
résultat de comparaison historique, pas une preuve sur v4. Documentation des
versions, du cache, des exemples et des limites dans `PROMPT_DESIGN.md`.

**Références :** compétence OpenAI Docs, guides officiels Prompt engineering et
Reasoning best practices consultés ; liens dans `PROMPT_DESIGN.md`. RCORCF est
la structure explicitement demandée par l'utilisateur. Aucun enrichissement
métier externe et aucune modification du modèle.

**Vérifications exécutées :** `unittest discover -s tests -q` : 62 tests passent.
Les nouveaux contrôles lisent les exemples directement dans le prompt et vérifient
leur JSON, labels, tickers, unicité, tri et preuves exactes. Un autre test vérifie
que chacun des deux tags invalide le cache indépendamment. Prévisualisation réelle
sur N001/N002/N027 réussie, réservation indicative cumulée 0,6177635 USD pour les
premières tentatives, sans appel ni dépense. Les clés diffèrent bien du pilote v2 ;
empreintes des deux entrées inchangées, liens Markdown et encodage vérifiés.

**Limites et suite :** aucun résultat API v4 produit ; la qualité sémantique reste
à mesurer. Les exemples ne sont pas un jeu de test indépendant, notamment Waymo,
inspiré d'une omission connue. Comparer la nouvelle version au pilote sur les
régressions et sur des articles distincts avec annotations humaines. Le détail
supplémentaire augmente la taille de la requête, sans garantie d'amélioration.
Coût et budget restant inchangés par rapport à l'entrée précédente.

## 2026-10-13 — retest du prompt RCORCF

**Demande :** « Bon reteste pour voir ca donne quoi ». Exécution sur les mêmes
trois articles pour comparaison directe avec v2, sans nouvelle modification
du prompt, du modèle, des paramètres ou du code.

**Commande :** `python -m aie2609 classify --ids N001 N002 N027 --max-cost-usd
4.5894004 --max-attempts 1 --output-dir output/pilot-005`, exécutée avec le venv
et l'accès réseau requis, après lecture des engagements précédents. Clé locale
non affichée. Modèle `gpt-5.6-terra`, prompt `entity-sentiment-v4-rcorcf`, effort low.

**Résultat :** trois réponses validées, trois appels, zéro reprise, zéro cache
local, neuf paires article/ticker. N001 et N002 conservent les mêmes tickers et
labels que v2. N027 ajoute GOOGL neutral à TSLA negative, avec preuve exacte
mentionnant Waymo. GS neutral est bien présent dans N002. Tableau détaillé dans
`REVIEW_SET.md` ; aucune modification manuelle des sorties.

**Consommation :** 40 884 tokens d'entrée, dont 9 332 en lecture cache et 31 543
en écriture cache ; 677 tokens de sortie. Coût rapporté : **0,0888659 USD**.
Coût connu cumulé des essais : **0,3257085 USD**. La réservation de 0,173757 USD
du premier échec réseau reste conservée ; engagement total **0,4994655 USD** et
solde prudent du budget utilisateur **4,5005345 USD**.

**Contrôles :** manifeste completed, bonne version, empreintes des requêtes
conformes au code courant, revalidation des neuf entrées, comparaison des labels
avec v2 et intégrité des deux sources vérifiée. Les 62 tests hors réseau étaient
déjà passés lors de la refonte ; aucune modification de code dans ce retest,
donc pas de nouvelle exécution de cette suite annoncée.

**Limite :** résultat favorable sur des cas connus, dont Waymo enseigné dans un
exemple du prompt. Pas de taux de précision généralisable ni de validation humaine
indépendante. Prochaine vérification de qualité : échantillon distinct avant un
traitement complet. Aucun article supplémentaire traité dans ce retest.

## 2026-10-13 — test de dix articles supplémentaires

**Demande :** tester dix exemples. Sélection de N003, N029, N054, N063, N064,
N070, N077, N084, N096 et N097, tous distincts des pilotes précédents. Lecture
complète et attentes provisoires consignées dans `docs/REVIEW_10.md` AVANT les
appels ; alternatives explicites pour les cas ambigus. Aucune validation humaine
indépendante revendiquée, aucun enrichissement métier externe.

**Exécution :** prompt v4 RCORCF, modèle imposé et effort low inchangés. Dry-run
réussi, réservations cumulées indicatives 2,0546625 USD. Premier run avec budget
restant 4,5005345 USD et une tentative par article dans `output/review-010` :
quatre succès puis rejet de N064, coût 0,1322405 USD. Aucun résultat complet
annoncé. Le motif précis n'étant pas journalisé, la cause de ce rejet ne peut
pas être établie rétrospectivement à partir des artefacts conservés.

**Correction limitée :** `runner.py` conserve désormais le diagnostic fixe du
validateur dans `validation_error` et le message terminal, sans réponse brute,
extrait ou secret. Nouveau test de non-divulgation ; 63 tests passent. Ni prompt,
schéma ni critères d'acceptation changés pour contourner l'échec.

**Reprise :** nouveau dossier `output/review-010-resume`, budget 4,368294 USD
après déduction du premier run, deux tentatives maximum configurées. Quatre
résultats repris du cache, six nouveaux appels tous valides. N064 a nécessité
deux appels au total ; aucun autre article n'a nécessité de reprise. Pas de
modification manuelle de classification ou de cache.

**Résultat :** dix articles terminés, 28 paires. Huit articles correspondent
aux attentes/alternatives préalables de l'agent. JPM manque dans N070 malgré le
nom de conférence, NWSA manque dans N077 malgré WSJ. NFLX negative est un
désaccord de sentiment à arbitrer face aux initiatives et difficultés décrites.
Les cas Unicode, neutralité des acteurs non affectés, homonymes Everpure et
liste vide N096 sont correctement traités selon cette revue provisoire.

**Coût :** 11 appels au total ; 0,1322405 + 0,1469120 = **0,2791525 USD**, rejet
compris. 149 790 tokens d'entrée (60 340 lecture cache, 89 417 écriture cache)
et 3 623 de sortie. Coût connu cumulé du projet **0,6048610 USD** ; réservation
inconnue antérieure **0,173757 USD** ; engagement total **0,7786180 USD** ; solde
prudent des 5 USD autorisés **4,2213820 USD**. Le rapport de la seule reprise
ne représente pas le coût complet des dix analyses.

**Contrôles :** 63 tests hors réseau passés après modification des diagnostics ;
manifeste terminé, dix identifiants distincts, empreintes de requêtes conformes,
revalidation des 28 entrées et de leurs preuves, intégrité des deux sources.
Fichier `.env` et résultats confirmés ignorés par Git. Aucun commit ou push.

**Suite :** faire arbitrer les cas signalés et améliorer le contrôle des mentions
secondaires avant le jeu complet. Prompt conservé tel quel pour que cette
évaluation reste comparable. Calcul et CSV finaux toujours au lot 3.

## 2026-10-13 — contrôle lexical et seconde passe sur dix articles

**Demande :** appliquer les améliorations proposées et vérifier les sorties.
Ajout de `review.py`, commande CLI `review`, points d'extension limités du runner
pour la requête et le rapport de différences. Indices de noms/tickers consultatifs,
validation stricte du fichier initial, cache séparé, même modèle et mêmes limites
de budget/reprises. Prompt de relecture `entity-review-v1`, règles lexicales
`explicit-name-ticker-v1` ; prompt de base v4 et normalisation inchangés.
Pas de dépendance supplémentaire, de délégation ou d'enrichissement externe.

**Tests :** `python -m unittest discover -s tests -q` avec le Python du venv :
71 tests passent. Huit nouveaux tests couvrent indices exacts, faux positifs de
mots courants, cache distinct selon la proposition, entrée invalide, relecture
simulée et cache, absence d'ajout forcé, suppressions/changements de label sans
mutation du résultat initial, et dry-run sans clé ni client réseau.

**Exécution :** `python -m aie2609 review --classifications
output/review-010-resume/classifications.json --dry-run`, puis même commande
sans dry-run avec `--max-cost-usd 4.221382 --max-attempts 2 --output-dir
output/verification-010`. Accès réseau autorisé pour l'appel réel, clé locale
non affichée. Dix appels terminés, aucune reprise, aucun cache local.

**Résultat :** ajout de NWSA neutral dans N077, mais suppression de P neutral
dans N084. JPM toujours absent de N070 ; Netflix toujours négatif dans N077.
28 paires, un ajout, une suppression, aucun changement de label. Régression
P signalée par `unresolved_hints_after`. Alertes NDAQ non pertinentes dans N003
et N070 ; les indices lexicaux ne constituent pas des réponses attendues.
Relecture non retenue automatiquement : résultats initiaux préservés, nouvelle
sortie candidate distincte, comparatif dans `docs/REVIEW_10.md`.

**Coût :** 141 562 tokens d'entrée (44 496 lecture cache, 97 036 écriture cache),
1 911 tokens de sortie ; **0,2744812 USD** additionnels. Cumul connu du projet
**0,8793422 USD** ; réservation inconnue **0,173757 USD** ; engagement total
**1,0530992 USD**, solde prudent **3,9469008 USD** sur les 5 USD autorisés.

**Contrôles :** manifeste completed, dix IDs distincts, dix clés de requête
recalculées conformes, 28 entités et leurs extraits revalidés, empreintes des
deux sources et de la première classification inchangées. Exclusions Git de
`.env`, `.cache/reviews` et des sorties confirmées. Aucun résultat retouché,
aucun commit/push. Documents de commandes, contrats, architecture, versions,
plan et revue mis à jour.

**Limites et suite :** cette seconde passe ne démontre pas de gain net de
couverture ; le même modèle peut renforcer ou introduire une erreur. Faire
arbitrer les cas signalés pour disposer d'une référence humaine, puis tester
une correction ciblée sans perdre les entités déjà justifiées. Pas de nouveau
run payant ni de traitement des 100 articles dans ce lot. Calcul et CSV restent
au lot 3.

## 2026-10-13 — alias versionnés et dernière relecture ciblée

**Objectif :** généraliser le contrôle sans construire une base exhaustive de
filiales. Ajout de `entity_aliases.json` avec relations certaines, Everpure ambigu
et noms empêchés en génération automatique. Les variantes juridiques continuent
de venir du CSV. `review` sélectionne les alertes par défaut ; `--all` maintient
le mode complet. Aucun alias ne produit directement une classification.

**Implémentation :** `entity-coverage-v2` émet des `candidate_tickers`, sépare
alias fiables et ambigus, reconnaît les tickers explicitement introduits par
« ticker » ou « symbol » et exclut la forme courte Nasdaq du matching de société.
`entity-review-v2-targeted` renforce la conservation des entités explicitement
justifiées. Registre empaqueté, version et empreinte tracées. Rapport de différences
passé au schéma 2 avec `review_reasons` et `alias_version`.

**Vérification hors réseau :** `python -m unittest discover -s tests -q` :
74 tests passent. Ajouts pour schéma du registre, relations WSJ/JPM, ambiguïté
Everpure, absence de faux NDAQ, sélection ciblée et mode `--all`. Le dry-run réel
sélectionne N070, N077 et N084 seulement. Réservation initiale prudente observée
sur le code final : 0,644086 USD.

**Exécution réelle :** `python -m aie2609 review --classifications
output/review-010-resume/classifications.json --max-cost-usd 3.9469008
--max-attempts 2 --output-dir output/targeted-review-003`. Trois appels, aucune
reprise, aucun cache local. Coût **0,0927612 USD** ; 43 025 tokens d'entrée,
9 976 lus et 33 040 écrits au cache fournisseur, 679 de sortie.

**Résultat :** JPM neutral ajouté à N070, NWSA neutral ajouté à N077, P neutral
conservé avec PNR negative et CMG neutral dans N084. Aucun NDAQ. Toutes les alertes
fiables sont couvertes ; l'ambiguïté Everpure reste tracée par conception. NFLX
reste negative, désaccord sémantique documenté plutôt que corrigé manuellement.
La relecture ciblée coûte 66 % de moins que la relecture générale précédente et
atteint les 30 paires attendues provisoirement après composition conceptuelle avec
les sept articles inchangés. Aucun fichier de résultat n'a été fusionné ou retouché.

**Contrôles :** manifeste completed, trois IDs, preuves revalidées, clés de
requête recalculées, empreintes de `news.json`, `sp500.csv`, du registre et du
résultat initial conformes. Sources intactes ; clé, caches et sorties ignorés par
Git. Aucun commit/push. Cumul connu **0,9721034 USD**, réservation inconnue
**0,173757 USD**, engagement **1,1458604 USD**, solde prudent **3,8541396 USD**.

**Limites et suite :** l'amélioration est établie sur trois alertes observées,
pas sur une nouvelle vérité terrain indépendante. Le registre n'est volontairement
pas exhaustif ; le modèle garde le rôle contextuel. Étape suivante autorisée par
le plan : agrégation temporelle et génération déterministe des CSV, en laissant
le choix de composition des propositions explicite.

## 2026-10-13 — test complet des 100 articles

**Demande :** tester les 100 articles avant le calcul des scores. Suite hors réseau
rejouée avant appel : 74 tests passaient. Dry-run : 100 requêtes potentielles,
réservation maximale théorique 20,5746125 USD ; contrôle réel séquentiel borné au
solde prudent 3,8541396 USD, avec arrêt avant dépassement.

**Première passe :** `classify --limit 100 --max-cost-usd 3.8541396
--max-attempts 2 --output-dir output/full-100-v4`. 100 articles, 87 appels,
13 résultats repris du cache, aucune reprise ou dépense inconnue. 217 paires :
70 positive, 93 neutral, 54 negative ; 11 listes vides. 1 186 925 tokens d'entrée
(401 276 lecture, 785 388 écriture cache) et 16 733 de sortie. Coût 2,2450432 USD.

**Défaut découvert :** le contrôle v2 signalait 45 articles, principalement parce
que `target`, `block`, `southern`, Rollins, `(MA)` et `(CMS)` étaient assimilés à
TGT, XYZ, SO, ROL, MA et CMS. Aucun appel de revue lancé sur cette liste bruitée.
Correction versionnée : `entity-aliases-v2`, `entity-coverage-v3`, suppression du
matching général des tickers parenthétiques et blocage des formes courtes ambiguës.
Ajout d'un test de non-régression ; **75 tests passent**. Huit alertes plausibles.

**Relecture ciblée :** `review --classifications output/full-100-v4/classifications.json
--max-cost-usd 1.6090964 --max-attempts 2 --output-dir
output/full-100-targeted-review`. Huit appels, aucune reprise/cache local,
0,2281222 USD. Ajouts : STT/N012 ; NWSA et WBD/N013 ; SBUX/N038 ; JPM/N070 ;
BLK/N076 ; NWSA/N077 ; IVZ/N091. Aucun changement pour N084, aucune suppression
ou modification de label. 115 346 tokens d'entrée (34 916 lecture, 80 406 écriture
cache) et 1 673 de sortie.

**Vérification :** deux manifestes completed, 100 IDs, 225 paires après composition
en mémoire (70 positive, 101 neutral, 54 negative), preuves et clés revalidées,
empreintes des sources, registre et première sortie conformes. L'ambiguïté N084
reste signalée mais P/PNR sont présents et distincts. Aucune fusion écrite ou
retouche manuelle. `.env`, caches et sorties ignorés ; sources intactes.

**Budget :** coût du lot 2,4731654 USD ; cumul connu projet 3,4452688 USD ;
réservation inconnue antérieure 0,173757 USD ; engagement prudent 3,6190258 USD ;
solde des 5 USD **1,3809742 USD**.

**Limite et suite :** validité structurelle complète, sans revue humaine exhaustive
des 100 sentiments. Rapport détaillé dans `docs/FULL_100_REVIEW.md`. Le lot 3 doit
composer explicitement les huit propositions avec les 92 lignes initiales, puis
calculer les poids temporels et écrire les CSV ; ne pas fusionner à la main.

## 2026-10-13 — préparation de la dernière passe complète

**Demande :** appliquer les petits ajustements issus de la revue sémantique puis
relancer les 100 articles avant la composition automatique.

**Changements :** `entity-sentiment-v5-rcorcf` précise qu'une performance
historique ou un faible mouvement de pair cité seulement comme comparaison reste
neutre. Il exige une implication propre à chaque partie d'un accord. Deux exemples
synthétiques couvrent ces règles. `entity-aliases-v3` ajoute CNN → WBD, relation
retrouvée pendant la relecture de N013. Aucun résultat existant n'est retouché.

**Vérification :** dry-run sur 100 articles sans clé ni réseau : 100 requêtes,
nouvelle version de prompt et nouvelles empreintes de cache ; réservation locale
maximale théorique 21,1006125 USD. La première exécution des 75 tests a révélé une
fixture N013 incomplète, corrigée pour inclure AMZN avant de tester l'alerte WBD.
Après correction, les **75 tests passent**.

**Exécution :** plafond relevé explicitement à 10 USD. Un premier appel bloqué
par le réseau conserve une réservation inconnue de 0,176203 USD. Une reprise
valide N001–N090 pour 2,3567970 USD, puis une passe à 512 tokens valide N091–N096
et facture aussi une réponse N097 incomplète, pour 0,1828785 USD. Le run cohérent
`output/full-100-v5-final`, à 1 024 tokens, reprend 90 caches et effectue dix
appels pour 0,1174879 USD. Manifeste completed, 100 articles et aucune réponse
invalide dans l'artefact final.

**Résultat :** 220 paires, dont 62 positive, 105 neutral et 53 negative ; 11 listes
vides. Comparaison à v4 + revue ciblée : 29 articles changent, sept ajouts, douze
retraits et 23 changements de label. Les corrections prévues N069/N091/N095 sont
obtenues. Régressions observées : deux faux XYZ pour le réseau social X, mentions
neutres perdues, BAC/N092 affecté par la dégradation de Nike et NVDA/N076 dominé
par un contexte favorable ancien. v5 n'est donc pas promue automatiquement.

**Vérification et budget :** schéma, 100 IDs, preuves exactes, univers, manifeste,
empreintes des sources et 75 tests hors réseau validés. Coût v5 connu 2,6571634
USD ; cumul connu 6,1024322 USD ; réservations inconnues 0,349960 USD ; engagement
prudent 6,4523922 USD sur 10 USD. Prochaine étape : composition déterministe avec
provenance et contrôles des ajouts suspects avant le calcul temporel.

## 2026-10-13 — composition contrôlée et audit croisé v4/v5

**Objectif :** matérialiser la composition v4 + relecture ciblée sans édition
manuelle, puis empêcher son utilisation pour le score tant que les omissions ou
associations manifestement douteuses ne sont pas résolues.

**Implémentation :** ajout de `composition.py` et de la commande hors réseau
`compose`. La base et la candidate doivent couvrir exactement les 100 articles.
Chaque superposition de revue doit être `completed`, référencer l'empreinte de la
base, posséder les mêmes IDs dans ses classifications et son rapport de changements,
et ne conserver aucune alerte fiable non résolue. La sortie garde la provenance
par article, compare les tickers et labels, et distingue alertes bloquantes et
consultatives. Deux revues du même article ou une collision de chemins sont refusées.

Le registre passe à `entity-aliases-v5`. Ajouts certains : CNBC/NBC News → CMCSA,
CBS/CBS News → PSKY, Barron's → NWSA et Kenworth → PCAR. Les rapprochements
`X → XYZ` et `SpaceX → XOM` sont explicitement interdits. Un contrôle consultatif
signale aussi un label non neutre fondé sur un extrait de recommandation d'analyste
qui ne nomme pas l'entité classée.

**Exécution :** `python -m aie2609 compose --news news.json --universe sp500.csv
--baseline output/full-100-v4/classifications.json --review-dir
output/full-100-targeted-review --candidate
output/full-100-v5-final/classifications.json --output-dir
output/composition-audit-v3`. Aucun chargement de clé et aucun appel réseau.

**Résultat :** 100 articles, 225 paires et huit articles issus de la revue. Le
rapport est `completed` au sens de la composition mais `ready_for_scoring=false`.
La composition porte sept alertes bloquantes sur six articles : CMCSA/N030,
CMCSA/N047, CMCSA-PSKY/N048, CMCSA/N061, NWSA/N066 et le faux XOM/N100 déduit
de SpaceX. La candidate v5 porte quinze alertes bloquantes et 29 désaccords avec
la composition ; les deux faux XYZ/N023 et N100 sont détectés. BAC/N092 apparaît
dans les alertes consultatives de transfert de rôle de la candidate.

**Vérification :** `python -m unittest discover -s tests -q` : **79 tests passent**.
`python -m compileall -q src tests` passe. L'audit réel confirme 100 articles,
503 lignes source, 500 entreprises canoniques et seulement les U+200B connus de
N027/N100. L'aide CLI expose `audit`, `classify`, `review` et `compose`. `.env`,
les caches et `output/` restent ignorés. Git n'est pas dans le PATH du terminal ;
le binaire local `.tools/mingit/cmd/git.exe` a donc servi aux contrôles, sans
commit ni push. Aucun appel API et aucun coût supplémentaire.

**Limite et suite :** les alertes d'ancrage sont volontairement consultatives car
un extrait exact peut employer un pronom ou une marque non enregistrée. Les sept
blocages doivent être arbitrés par une règle ou une relecture reproductible ; le
calcul temporel et les CSV restent interdits jusque-là.

## 2026-10-13 — résolution stricte des six blocages

**Décision :** la première relecture des six articles a coûté 0,1741450 USD et
retrouvé toutes les sources, mais elle a aussi changé GS/MS dans N047, AMZN dans
N048 et supprimé SCHW/N066. Le run est structurellement valide mais rejeté comme
superposition : aucune de ces modifications ne faisait partie du besoin de
couverture.

**Durcissement :** `review --ids` permet une sélection explicite validée contre
le fichier initial. `review --additions-only` complète le prompt et surtout
rejette côté Python toute suppression ou modification de label, y compris depuis
le cache. `compose` recalcule désormais chaque diff et vérifie qu'il correspond
exactement à `review_changes.json`; il impose aussi le contrat additions-only
indiqué par le manifeste.

**Exécution :** les réponses conformes N030/N047/N048/N061 ont été rejouées depuis
le cache dans `output/composition-additions-review-4`. N066 a demandé deux appels
bornés et 0,0105296 USD avant de conserver SCHW et d'ajouter NWSA. N100 a été
isolé dans `output/composition-n100-review-cached` : zéro nouvel appel, retrait
de XOM seulement. Une tentative N100 précédente a subi une erreur réseau avant
usage mesurable ; sa réservation de 0,179378 USD reste inconnue. Le run
additions-only interrompu a coûté 0,1467906 USD, malgré quatre réponses ensuite
réutilisées, car N066 a été rejeté par le validateur.

**Résultat :** `output/composition-final-v2/` est reproductible et
`ready_for_scoring=true` : 100 articles, 230 paires, 70 positive, 106 neutral,
54 negative, 11 articles vides, zéro alerte bloquante. Écarts exacts avec la
composition précédente : ajouts CMCSA/N030, CMCSA/N047, CMCSA-PSKY/N048,
CMCSA/N061, NWSA/N066, tous neutral ; retrait XOM/N100 ; aucun changement de label.
Les 60 alertes d'ancrage restantes sont consultatives et n'identifient aucune
omission fiable ou association interdite.

**Vérification :** **81 tests passent**, `compileall` passe, les classifications
des compositions finales v1 et v2 ont la même empreinte SHA-256, et les sorties,
caches et `.env` restent ignorés. Coût additionnel connu de la phase : 0,3314652
USD. Cumul : 6,4338974 USD connus + 0,529338 USD réservés/inconnus = 6,9632354 USD ;
solde prudent 3,0367646 USD sur 10 USD. Prochaine étape : implémenter la formule
temporelle et les deux CSV à partir de cette composition seulement.

## 2026-10-13 — calcul temporel et génération des CSV

**Objectif :** transformer uniquement la composition approuvée en livrables du
sujet, sans clé ni appel réseau. `composition_report.json` contient maintenant
l'empreinte du JSON composé ; l'export refuse un rapport non prêt ou une empreinte
différente.

**Implémentation :** ajout de `scoring.py`, version `time-decay-v1`, et de la
commande `export`. Les dates sont converties en UTC avant soustraction à
`2026-09-29T00:00` New York. Le poids est `0.5 ** (days / 7)`, les labels valent
`+1/0/-1`, et `math.fsum` assure une addition stable. Une date future est refusée.
Les CSV UTF-8 sont écrits atomiquement, triés, avec les colonnes exactes ; le
manifeste completed conserve paramètres, comptages et empreintes des sources et
sorties.

**Exécution :** régénération déterministe dans `output/composition-final-v3/`,
puis `export --composition-dir output/composition-final-v3 --output-dir
output/final-results-v1`. Résultat : 100 articles, 230 lignes dans `entities.csv`,
111 tickers dans `scores.csv`, dont 26 scores nuls. Les empreintes du manifeste
ont été recalculées et comparées aux fichiers.

**Vérification :** **86 tests passent**. Les nouveaux cas couvrent les poids à
0, 7 et 14 jours, une demi-semaine, le passage à l'heure d'été mesuré comme
23 heures réelles, l'annulation exacte, une entreprise seulement neutre, une date
future et le contrat d'export. Contrôle indépendant : en-têtes, ordre, unicité des
230 couples, finitude des 111 valeurs et empreintes conformes. L'audit des sources
reste inchangé et `compileall` passe. Aucun coût API supplémentaire.

**Résultat observable :** premiers scores positifs GOOGL 1,32508111, AMD
1,00838430, UAL et DAL 0,91673726 ; premiers scores négatifs NKE -1,39104223,
BX -0,96839708, BA -0,93998803 et TSLA -0,88239668. Ces agrégats décrivent
uniquement les articles fournis et ne constituent pas une recommandation.

## 2026-10-13 — échantillon humain des désaccords

**Objectif :** rendre visibles les différences sémantiques encore ouvertes et
permettre une évaluation humaine simple, sans promouvoir automatiquement v4 ou v5.

**Implémentation :** ajout de `evaluation.py` et des commandes hors réseau
`prepare-evaluation` et `evaluate`. Une différence de présence devient le label
`absent`; les décisions humaines acceptées sont `positive`, `neutral`, `negative`,
`absent` et `uncertain`. Les cellules provenant des articles sont protégées contre
l'exécution de formules lors d'une ouverture dans un tableur.

**Artefacts :** `review/human-evaluation-v1/disagreements.csv` expose 39 décisions
différentes sur 27 articles. `sample.csv` contient dix cas couvrant comparaison
historique, concurrent secondaire, accord commercial, banque analyste et article
multi-entreprises. `SAMPLE_GUIDE.md` présente les articles complets et les deux
propositions. Les colonnes humaines sont initialement vides.

**Usage :** renseigner `human_decision` et éventuellement `human_notes`, puis
exécuter `python -m aie2609 evaluate --sample
review/human-evaluation-v1/sample.csv`. Le rapport indique cas répondus, incertains,
restants et accord de chaque version. Aucune annotation n'est appliquée aux CSV.

**Documentation :** le README a été réécrit autour de l'état actuel, des commandes
essentielles, de la revue humaine et des limites. L'historique détaillé reste dans
ce journal et `FULL_100_REVIEW.md`. Les **88 tests hors réseau passent**,
`compileall` passe et la commande `evaluate` valide l'échantillon vide en indiquant
10 décisions restantes, sans inventer de mesure de précision.

## 2026-10-14 — commande de bout en bout

**Constat d'audit :** le sujet exige une commande exécutable par les évaluateurs.
Il fallait enchaîner `classify`, `review`, `compose` et `export` à la main. En
simulant hors réseau le code actuel, la composition de la passe v5 portait
15 alertes bloquantes et `export` refusait d'écrire les CSV. Aucune des 100 requêtes
du prompt actif n'était dans le cache local (clé différente : 4 096 tokens de
sortie au lieu de 1 024).

**Implémentation :** `pipeline.py` et la commande `run`. Les étapes existantes sont
réutilisées telles quelles, chacune dans son sous-dossier. Seuls les articles avec
une alerte bloquante sont relus, avec un mode par cause : `additions-only` pour
une omission fiable, relecture ciblée pour un alias interdit, comme pour
N030–N066 et N100. Une relecture invalide ou laissant un indice fiable non résolu
est rejetée et la première passe est conservée. `export_scores(allow_alerts=True)`
permet au seul run d'écrire les CSV avec `ready_for_scoring: false`. La commande
`export` reste stricte. `run_report.json` agrège appels, tokens connus, coût et
coût par article.

**Vérification :** `python -m unittest discover -s tests` : **92 tests passent**
(quatre nouveaux). Répétition hors réseau sur les 100 articles réels avec un faux
client rejouant les réponses v5, dans un dossier temporaire avec un cache séparé :
114 appels simulés, les 15 alertes bloquantes connues sont relues dans le bon mode
(13 `additions-only`, 2 ciblées), puis composition et export aboutissent à
`completed_with_alerts`, 220 paires et 110 tickers. `run` sans `--max-cost-usd`
est refusé ; `--dry-run` fonctionne sans clé ; `export` refuse toujours une
composition non prête. Aucun appel API ni coût.

**Limites et suite :** les CSV de `output/final-results-v1` ne sont pas encore
produits par `run`. Un run réel coûterait environ 2,6 USD pour la classification
(environ 0,026 USD par article mesuré sur v4/v5), plus environ 0,03 USD par
relecture. Solde prudent sur les 10 USD autorisés : environ 3,04 USD.

## 2026-10-14 — run réel de bout en bout

**Commande :** `python -m aie2609 run --max-cost-usd 4 --output-dir
output/run-final-v1`, avec un budget accordé explicitement par l'utilisateur pour
terminer le run.

**Résultat :** `completed`, code de sortie 0. Classification : 101 appels pour
100 articles, une réponse invalide sur N064 refusée puis redemandée, 2,6307188 USD.
Treize articles avaient une alerte bloquante : douze omissions relues en
`additions-only` (STT, NWSA, WBD, SBUX, BLK, CMCSA, GS) et un faux `XYZ` dans N100
relu en mode ciblé. Toutes les relectures ont été appliquées en un appel chacune,
pour 0,3880509 USD. Composition : zéro alerte bloquante, 65 alertes consultatives,
`ready_for_scoring=true`. Sorties : 232 paires (63 positive, 119 neutral,
50 negative), 112 tickers, dont 34 scores nuls. Total : 114 appels,
**3,0187697 USD, soit 0,030187697 USD par article**, sans cache local ni coût inconnu.

**Contrôles indépendants :** en-têtes exacts, aucun ticker hors référentiel, aucun
doublon, scores recalculés avec un écart maximal de 0,0.

**Comparaison avec l'ancienne composition manuelle `final-results-v1` :**
19 paires diffèrent. Neuf labels positifs et quatre négatifs deviennent neutres
(petits mouvements de pairs dans N091, NVDA/N069, AAPL/N095, GS-MS/N047, ADBE/N039…),
deux neutres deviennent positifs (C et JPM dans N071), trois neutres sont ajoutés
et un retiré. Sur l'échantillon humain de dix cas disputés, `run-final-v1`
concorde 4 fois sur 10, contre 8 sur 10 pour l'ancienne composition. Cet
échantillon a été choisi parmi les désaccords v4/v5 ; il n'est pas représentatif
de la précision globale. Il indique toutefois que la règle v5 sur les mouvements
de pairs incidents neutralise des cas que l'annotateur juge directionnels.

**Budget :** cumul connu 9,4526671 USD ; réservations inconnues antérieures
0,529338 USD ; engagement prudent 9,9820051 USD.

## 2026-10-14 — visibilité de l'usage LLM

**Demande :** rendre visibles appels, tokens et coût, exigence du sujet.

**Implémentation :** `summarize_usage` et `format_usage` dans `usage.py` ; commande
hors réseau `usage --run-dir` (dossier `run` ou ancien run d'une seule étape) ;
`run_report.json` contient désormais tokens, coût par catégorie et par étape ;
`run` affiche ce résumé en fin d'exécution. Un avertissement apparaît lorsque des
résultats proviennent du cache local, car le coût par article n'est alors pas
celui d'un run complet.

**Vérification :** **93 tests passent**. `usage` sur `output/run-final-v1` : 114
appels, 1 reprise, 1 615 380 tokens d'entrée (579 371 lus, 1 035 667 écrits au
cache, 342 ordinaires), 26 087 tokens de sortie, 3,0187697 USD, 0,030187697 USD par
article. La somme des catégories est égale au coût enregistré. Sur
`output/full-100-v4`, l'avertissement de 13 résultats rejoués s'affiche. Aucun appel API.

**Constat :** 86 % du coût vient de l'écriture au cache fournisseur. Ce n'est pas
optimisé ; ce point est documenté dans `ARCHITECTURE.md`.

## 2026-10-14 — CLAUDE.md et prompt v6 avec rôles

**CLAUDE.md :** contexte Claude Code qui importe `AGENTS.md` (`@AGENTS.md`) au lieu
de le dupliquer. Il ajoute ce qui ne se déduit pas du code : quoi lire et quand,
commandes exactes de l'environnement Windows, Git hors PATH et propriétaire
différent, pièges déjà payés (clé de cache, régressions de prompt, coût du cache
fournisseur) et définition de « terminé ».

**Objectif v6 :** réduire les erreurs sur la frontière implication/mention, cause de
la quasi-totalité des 19 désaccords entre les deux versions candidates.
`run-final-v1` reste la solution de repli, inchangée.

**Implémentation :** prompt `entity-sentiment-v6-roles`, champ `role`, schéma strict
à deux branches `anyOf` avec `$defs` pour l'énumération des tickers, validation
`require_role=True` pour les réponses en direct. Les anciens artefacts sans rôle
restent lisibles. Registre `entity-aliases-v6`. Détails dans `PROMPT_DESIGN.md`.

**Vérification :** **95 tests passent**. Les 13 exemples du prompt sont validés avec
leurs rôles. Le dry-run construit les 100 requêtes ; la taille des requêtes reste
d'environ 55 000 caractères, comme en v5. Aucun appel API à ce stade : la
compatibilité de `anyOf`/`$defs` avec le modèle doit être confirmée par un pilote.

## 2026-10-14 — pilote v6, échec N064, vote et référence

**Budget :** l'utilisateur autorise jusqu'à 100 USD au total pour le projet.

**Pilote v6 :** `classify --ids N039 N047 N058 N091 N095 --max-cost-usd 1
--output-dir output/pilot-v6-roles` : 5 appels, 0,1532555 USD, aucune réponse
invalide. Le schéma `anyOf`/`$defs` est accepté par l'API. Rôles observés : GS/MS
N047 `comparison`, NFLX/GOOGL/RDDT N091 `comparison`, AAPL N095 `counterparty`,
TTWO N058 `subject/positive`. MSFT/Xbox absent dans la classification seule, ce
qui déclenchera une relecture dans `run`.

**Run v6 à une passe :** `run --max-cost-usd 6 --output-dir output/run-v6-roles` :
échec contrôlé à l'étape `classify` après 63 articles et 1,5984818 USD. N064 a cité
deux fois un extrait non exact ; le validateur l'a refusé et aucun résultat n'a été
inventé. Ce dossier reste comme preuve ; les 63 réponses validées sont en cache.

**Correctifs :** une tentative refusée est redemandée avec le motif fixe du
validateur (`with_validation_feedback`, jamais le texte rejeté). `--passes 3` ajoute
des passes indépendantes via des répliques de cache et un vote majoritaire strict,
avec égalité → `neutral` signalé. `prepare-reference` et `score-reference`
construisent une référence humaine à l'aveugle et estiment l'exactitude par
version. **100 tests passent.**

**Run lancé :** `run --passes 3 --max-attempts 3 --max-cost-usd 15 --output-dir
output/run-v6-vote3` (résultats dans l'entrée suivante).

## 2026-10-14 — run v6 en trois passes et référence à arbitrer

**Commande :** `run --passes 3 --max-attempts 3 --max-cost-usd 15 --output-dir
output/run-v6-vote3`. Statut `completed`, zéro alerte bloquante, 233 paires
(61 positive, 117 neutral, 55 negative), 112 tickers. 278 appels, 5 reprises,
65 réponses reprises du cache local (le run interrompu et le pilote). N064 a été
refusé une fois puis validé grâce au retour du motif. Coût du run : 2,9692577 USD.

**Coût :** les passes 2 et 3 coûtent environ 0,006 USD par article contre 0,026 USD
pour une passe à froid. Le préfixe commun (consignes, univers et schéma, environ
14 000 tokens) est alors lu dans le cache fournisseur au lieu d'y être écrit. Coût
complet estimé d'un run à trois passes à froid : environ 4,5 USD, soit 0,045 USD
par article.

**Stabilité :** 224 couples sur 239 sont identiques dans les trois passes (93,7 %).
Les écarts entre deux passes vont de 9 à 11 couples. Vote : 224 unanimes,
9 majoritaires, 0 égalité, 6 couples proposés par une seule passe et écartés
(CRWD/N010, XYZ/N023, GM/N038, MCO/N051, BBY/N099, RDDT/N100). Rôles du vote :
108 sujets directionnels sur 233 paires, 104 mentions toujours neutres
(38 autres mentions, 27 comparaisons, 22 émetteurs de note, 17 sources).

**Écarts entre versions :** manuel/run-final-v1 19, run-final-v1/v6-vote3 10,
v6-passe1/v6-vote3 4 ; 28 couples disputés entre les quatre versions candidates.

**Référence :** `prepare-reference` avec six versions (manuel, run-final-v1, les
trois passes v6 et le vote) : 239 couples, 203 unanimes, 36 disputés, plus
25 contrôles aléatoires du consensus, soit 61 cas dans `review/reference-v1/`. Le
CSV ne contient plus que les colonnes à remplir. **100 tests passent.**

**Budget cumulé :** 14,1736621 USD connus + 0,529338 USD de réservations
inconnues anciennes = 14,7030001 USD sur les 100 USD autorisés.

## 2026-10-14 — arbitrage, choix de la version livrée

**Arbitrage :** l'utilisateur a demandé à l'agent d'arbitrer les 61 cas plutôt que de
le faire à la main. Décisions et limites dans `review/reference-v1/README.md` :
arbitre Claude et non un humain, définitions du sujet, `key.json` ouvert seulement
après le score, quelques labels déjà vus en conversation (N039, N047, N091, N095),
21 décisions notées discutables.

**Score :** `score-reference --dir review/reference-v1`. Exactitude estimée :
manuel 0,878, run-final-v1 0,907, passes v6 0,920 à 0,924, **v6-vote3 0,933**.
Cas disputés justes sur 36 : 15, 22, 25-26 et 28. Le classement tient sans les cas
discutables : 9, 17, 16-17 et 19 sur 20. Contrôles du consensus : 24 sur 25.

**Décision :** livrer `output/run-v6-vote3/final/`. `run` prend par défaut cette
configuration (`--passes 3`, `--max-attempts 3`). Contrôle indépendant des CSV
retenus : en-têtes exacts, 233 lignes, aucun ticker hors référentiel ni doublon,
scores recalculés avec un écart de 0,0, manifeste `completed` et
`ready_for_scoring=true`. **100 tests passent.**

**Limites :** la référence n'est pas humaine ; elle ne mesure pas les omissions
partagées par toutes les versions. Les erreurs restantes de la version retenue
portent surtout sur des cas limites (GS/MS N047, PCG N020, RCL N049/N055, JBL N088).

## Format des entrées suivantes

Pour chaque lot : objectif ; changements ; décisions et alternatives utiles ;
commandes de vérification réellement exécutées et résultats ; limites ; prochaine
étape. Consigner toute modification de prompt et sa motivation. Ne pas y stocker
de clé, réponse API brute ou longue copie d'article.
