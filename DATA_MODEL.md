# Contrats de données

Statut : contrat d'implémentation initial. Les exigences de sortie et de calcul
proviennent du sujet, page 4 ; les politiques d'erreur ci-dessous sont nos choix.

## Entrées

`news.json` : tableau d'objets avec `id`, `date`, `headline`, `body`, tous chaînes
non vides. `id` doit être unique ; `date` suit exactement `YYYY-MM-DDTHH:MM`, en
heure locale de New York. Le jeu fourni contient 100 articles ; le chargeur sera
générique et ne codera pas ce nombre en dur.

`sp500.csv` : colonnes `symbol,security,gics_sector,headquarters,date_added`.
Le ticker et le nom sont requis pour classifier ; les autres colonnes sont des
métadonnées. Aucun ticker ne peut être déduit de l'appartenance actuelle réelle
au S&P 500 : le fichier fourni définit l'univers. Il contient 503 lignes.

Politiques prévues : UTF-8 (BOM initial toléré), rejet des champs requis manquants,
des types incorrects, des clés JSON dupliquées, des colonnes CSV dupliquées,
des lignes mal formées, des symboles dupliqués et des identifiants d'article
dupliqués. Champs supplémentaires : les signaler et les ignorer explicitement.
Refuser des entrées vides et toute erreur de date avant de dépenser des tokens.

## Normalisation et identité

- Conserver les sources ; conserver texte brut et texte normalisé séparément en mémoire.
- Normaliser en Unicode NFC et les fins de ligne ; retirer U+200B détecté dans
  les noms/tickers en enregistrant l'anomalie. Ne pas supprimer arbitrairement
  tous les caractères Unicode de format ni translittérer les noms.
- Enlever les espaces de bord des champs structurants ; ne pas supprimer la
  ponctuation du texte ou de tickers tels que `BRK.B`.
- Détecter des contenus répétés et les signaler. Des identifiants distincts restent
  des articles distincts dans l'agrégation du sujet ; ne pas les fusionner en silence.
- Appliquer les correspondances `GOOG → GOOGL`, `FOX → FOXA`, `NWS → NWSA` ;
  `BRK.B` est la classe imposée. Un alias de classe n'autorise aucune sortie hors univers.
- Une entreprise canonique ne possède qu'une ligne par article. Les doublons de
  classification sont des erreurs à résoudre, surtout lorsque les labels diffèrent.

## Dates et agrégation

Interpréter les dates via `America/New_York`. Refuser une heure locale ambiguë ou
inexistante plutôt que de choisir silencieusement un décalage. Documenter la
disponibilité de `tzdata` pour Windows. Convertir les instants en UTC avant de
soustraire afin de mesurer la durée réelle, y compris aux changements d'heure.

```text
as_of = 2026-09-29 00:00 America/New_York
days = (as_of_utc - article_date_utc).total_seconds() / 86400
weight = 0.5 ** (days / 7)
label_value = {positive: +1, neutral: 0, negative: -1}
value(ticker) = somme(label_value × weight)
```

Choix : refuser les articles postérieurs à `as_of` avec une erreur explicite,
sans tronquer leur âge à zéro. Aucune moyenne, normalisation par nombre d'articles
ou pondération supplémentaire. Ne pas arrondir les contributions intermédiaires.
Addition stable avec `math.fsum` ; sérialisation décimale de précision suffisante
pour reconstruire le flottant, jamais `NaN`/infini et pas de zéro négatif.

## Réponse modèle interne — lot 2

Objet strict contenant une liste `entities`. Chaque élément : `ticker`, `label`
et `evidence` (court extrait exact du texte normalisé). L'identifiant d'article
vient du code, pas du modèle. Une liste vide est autorisée lorsqu'aucune entreprise
de l'univers n'est identifiée ; elle doit apparaître comme article traité dans le
manifeste. Valider tous les champs et refuser les champs inattendus du modèle.

L'extrait reste interne ; le CSV final ne gagne aucune colonne. Il peut documenter
une mention neutre. La présence de l'extrait ne prouve pas la relation filiale/parent
ni la classification ; ces points font partie de la revue humaine.

Le schéma transmis impose les tickers canoniques autorisés et les trois labels.
Le validateur vérifie également que l'extrait fait entre 1 et 500 caractères et
figure tel quel dans le titre ou le corps normalisé ; un doublon canonique est
refusé. Le tri final des entités est par ticker. Le prompt initial est versionné
`entity-sentiment-v1` ; le pilote retenu utilise `entity-sentiment-v2`.
Le prompt actif est `entity-sentiment-v5-rcorcf`, vérifié hors réseau et exécuté
sur les 100 articles, avec le même contrat de sortie. Les réponses incomplètes
et refus du modèle sont des erreurs. Le validateur structurel ne détecte pas les omissions.

## Artefacts de classification — lot 2

- `classifications.json` : `schema_version: 1`, tableau `articles`, chaque article
  ayant `id` et `entities`. Une liste vide y est conservée. Ce fichier n'est écrit
  qu'après validation de toute la sélection ; il ne remplace pas les CSV à livrer.
- `usage.json` : `schema_version: 1`, tarifs et date de vérification, compteurs
  d'appels et de cache local, tokens connus, coûts connus, coûts inconnus, budget
  et détail par tentative. Les montants USD sont des chaînes décimales ou `null`.
  Le coût par article sans cache n'est calculé que pour une sélection entièrement
  traitée sans cache local et sans coût inconnu.
- `run_manifest.json` : `schema_version: 1`, statut `running`, `completed` ou
  `failed`, modèle, version du prompt, empreintes des deux sources, identifiants
  sélectionnés et prévisualisation des réservations et clés de cache.

Le manifeste fait foi pour le succès. Les écritures utilisent un fichier temporaire
puis un remplacement atomique par fichier. Un arrêt brutal peut laisser `running`
et une tentative `in_flight` : ce n'est pas un résultat complet. Les dossiers de
run doivent être nouveaux et distincts du cache et des entrées.

## Relecture expérimentale — extension du lot 2

La commande `review` accepte un `classifications.json` initial, strictement validé
contre les articles et l'univers courants. C'est un artefact dérivé des deux
sources, pas un enrichissement métier externe. Son empreinte est ajoutée au
manifeste. Le résultat conserve le même schéma de classification dans un nouveau
dossier ; il n'écrase ni ne fusionne la première analyse.

La version ciblée produit `review_changes.json` avec `schema_version: 2`,
`review_version`, `coverage_version`, `alias_version` et `articles`. Pour chaque
`id` : `coverage_hints` (`candidate_tickers`, `kind`, `field`, `mention`, `excerpt`
et éventuellement `alias_type`), `review_reasons`, `missing_before`,
`unresolved_hints_after`, `added`, `removed` et `label_changes` (`ticker`, `before`,
`after`). Plusieurs `candidate_tickers` signifient une ambiguïté à résoudre, pas
plusieurs ajouts. Les listes d'indices manquants sont des alertes lexicales, pas
une liste d'erreurs certifiées. Les changements d'extrait seuls ne sont pas
répertoriés comme changements de label ; chaque version conserve ses preuves.

La réussite du run atteste la validation structurelle ; la justesse et l'intérêt
de la proposition doivent être évalués séparément avant de la retenir.

Avec `review --additions-only`, le prompt demande de préserver toutes les entités
et tous les labels initiaux, puis le validateur impose cette propriété sur la
réponse et sur tout cache relu. Une suppression ou un changement de label est une
réponse invalide, jamais une correction silencieuse.

## Composition contrôlée — lot 3

`compose` lit une classification complète de référence, zéro ou plusieurs dossiers
de revue terminés et, facultativement, une classification candidate complète.
Une revue n'est appliquée que si son manifeste référence l'empreinte de la base,
si ses IDs correspondent à `review_changes.json` et si aucune alerte fiable n'y
reste non résolue. Deux revues ne peuvent pas remplacer le même article.

Le dossier produit contient :

- `classifications.json`, schéma 1, résultat complet composé sans retouche manuelle ;
- `composition_report.json`, schéma 1, version de composition, empreintes et
  provenance par article, alertes bloquantes ou consultatives, et différences
  de tickers/labels avec la candidate.

Les omissions issues d'un alias certain et les alias explicitement interdits sont
bloquants. L'absence d'ancrage exact, l'ambiguïté et un possible transfert de rôle
analyste sont consultatifs car le langage peut employer un nom abrégé ou un pronom.
`ready_for_scoring` n'est vrai que sans alerte bloquante dans la composition ou
la candidate et sans désaccord avec cette candidate lorsqu'elle est fournie.
La composition vérifie également que `added`, `removed` et `label_changes` dans
chaque rapport de revue correspondent exactement aux classifications associées.

## Exports imposés

| Fichier | Colonnes exactes | Contraintes |
| --- | --- | --- |
| `entities.csv` | `id,ticker,label` | Une ligne par paire article/entreprise canonique ; identifiant existant ; ticker autorisé ; label `positive`, `neutral` ou `negative` |
| `scores.csv` | `ticker,value` | Une ligne pour chaque ticker présent dans `entities.csv`, y compris ceux dont le score vaut zéro |

Écrire en UTF-8, en-tête obligatoire, sans index ajouté, avec le module CSV pour
gérer l'échappement. Ordre : `(id, ticker)` pour entities, `ticker` pour scores.
Un run valide sans entité produit deux fichiers contenant leurs seuls en-têtes.
Une erreur ne doit jamais être confondue avec ce cas valide.

Les exports sont implémentés par `time-decay-v1`. `export` exige une composition
avec `ready_for_scoring=true` et une empreinte de `classifications.json` conforme.
Le manifeste final enregistre la référence, le fuseau, la demi-vie, les comptages
et les empreintes SHA-256 des sources et des deux CSV.

## Évaluation humaine

`prepare-evaluation` développe chaque différence de présence ou de label entre
deux classifications complètes en une décision `(id, ticker)`. `sample.csv`
contient le titre, l'article, les deux propositions et deux colonnes éditables :
`human_decision` et `human_notes`. Une décision vaut `positive`, `neutral`,
`negative`, `absent`, `uncertain` ou reste vide. `evaluate` ignore les valeurs
vides et incertaines pour le calcul d'accord et ne modifie aucun résultat.
