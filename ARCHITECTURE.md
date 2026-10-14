# Architecture

Statut : ingestion, audit, classification, composition contrôlée, calcul temporel
et exports CSV implémentés et testés hors réseau.
Accès API confirmé le 13 octobre ; 100 articles traités avec v4, puis huit alertes
relues de façon ciblée. Résultats et limites dans `docs/FULL_100_REVIEW.md`.
Le lot 3 est terminé ; l'analyse finale et la remise restent à préparer.
Exigences : sujet local, pages 2 à 5. Choix : pipeline séquentielle, fichiers
locaux, peu de dépendances, aucune interface web ni service permanent.

## Flux prévu

```text
JSON + CSV → validation / normalisation → univers canonique
          → classification par article → validation des réponses
          → agrégation déterministe → CSV + métriques + manifeste
                         ↕
                    cache local
```

## Répartition des responsabilités

| Étape | Responsable | Justification |
| --- | --- | --- |
| Lecture, schémas d'entrée, Unicode et dates | Code | Règles déterministes et testables |
| Univers autorisé et doubles classes | Code | Empêcher les tickers inventés et doubles comptes |
| Identification contextuelle, marques/filiales, sujet versus mention, sentiment par entreprise | `gpt-5.6-terra` | Nécessite une compréhension du contexte de l'article |
| Validation du schéma, tickers, labels, preuves et doublons | Code | Une réponse du modèle n'est pas une donnée de confiance |
| Pondération, addition, tri et écriture | Code | Formule imposée ; résultat mathématique reproductible |
| Arbitrages ambigus et analyse de qualité | Revue humaine assistée | Les contraintes de structure ne prouvent pas la justesse sémantique |

## Modules

Au lot 1, `cli.py` orchestre l'audit et traduit les erreurs de données en code de
sortie 2 ; `ingestion.py` charge et valide les deux sources, `normalization.py`
prépare une copie sûre, `dates.py` traite New York et `audit.py` construit le rapport.

Au lot 2, `classification.py` porte le prompt, le schéma et les validations ;
`llm.py` assure le transport HTTPS Responses avec `urllib` de la bibliothèque
standard, sans dépendance SDK supplémentaire. `usage.py` porte tarifs, tokens et
budget en `Decimal`. `runner.py` gère la sélection déjà chargée, les tentatives,
le cache, les résultats internes, le manifeste et les métriques durables.
`composition.py` valide les superpositions de revue, conserve leur provenance,
compare une candidate et bloque le scoring sur les alertes fiables. `cli.py`
expose `classify`, `review`, `compose`, `export` et `--dry-run`. `scoring.py`
applique la formule fixe, vérifie le rapport de composition et produit les
livrables CSV avec leur manifeste.

`pipeline.py` porte la commande `run` : il enchaîne `Classifier`, une relecture
par article bloqué (`additions-only` pour une omission, relecture ciblée pour un
alias interdit), `compose` sans candidate puis l'export. Le budget est commun à
toutes les étapes. Une relecture rejetée laisse la première passe validée, et
l'export final accepte des alertes restantes en les inscrivant dans les manifestes
(`completed_with_alerts`) : un livrable avec alertes visibles vaut mieux qu'une
absence de CSV pour un évaluateur. Les erreurs de transport, budget et coût
inconnu restent fatales.

Avec `--passes 3`, `pipeline.py` répète trois fois cette chaîne avec des répliques de
cache distinctes (`replica` entre dans la clé ; la réplique 0 partage le cache
ordinaire), puis `majority_vote` garde les couples proposés par une majorité stricte
avec leur label majoritaire. Une égalité de label devient `neutral` et elle est
comptée. Le vote est ensuite composé et exporté comme une passe unique. C'est un
choix de fiabilité contre coût : il réduit la variance d'un tirage et donne un
niveau d'accord par couple, pour environ trois fois le coût.

Le prompt v6 ajoute un rôle par entreprise ; le schéma à deux branches `anyOf`
interdit tout label autre que `neutral` pour les rôles que le sujet définit comme
neutres. Une réponse refusée est redemandée avec le motif fixe du validateur.

`reference.py` construit une référence humaine à l'aveugle (tous les désaccords
entre versions et des contrôles aléatoires du consensus) et estime l'exactitude
de chaque version. Le modèle n'y intervient pas.

`evaluation.py` compare deux propositions sans en désigner une comme vérité,
prépare un échantillon humain éditable et mesure ensuite leur accord avec les
décisions renseignées. Cette évaluation ne modifie jamais les classifications.

`review.py` ajoute une seconde passe facultative, séquentielle, avec le même modèle.
Le code recherche les noms du référentiel, leurs formes sans suffixe juridique et
les tickers explicitement balisés. Ces indices sont consultatifs : aucun préfiltre,
aucun ajout automatique et aucun label décidé par correspondance lexicale.
L'article et le référentiel complets restent transmis. Les propositions initiales
et les indices sont des données non fiables dans un message distinct.
`ReviewClassifier` réutilise les protections du runner et produit un rapport des
différences, avec un cache séparé dont la clé inclut aussi la proposition initiale.
Ce n'est pas une validation indépendante : le modèle peut maintenir une erreur ou
introduire une régression. L'essai sur dix articles a récupéré NWSA mais perdu P ;
ses résultats restent séparés de la première passe et soumis à la revue.

La version 2 charge `entity_aliases.json`, configuration applicative versionnée et
incluse dans les empreintes du run. Les variantes de noms juridiques sont générées
à partir du référentiel ; seules quelques relations certaines et ambiguïtés utiles
sont configurées. Un alias certain absent de la proposition ou toute ambiguïté
sélectionne l'article pour `review`. L'option `--all` conserve le diagnostic large.
Les alias ne créent aucune entité ni aucun label dans le code. Le dernier test
ciblé résout les deux omissions et préserve les deux Everpure, avec un désaccord
de sentiment NFLX encore explicite.

Le passage aux 100 articles a révélé que les formes courtes de sociétés peuvent
être des mots ordinaires ou des noms de personnes. `entity-coverage-v3` bloque ces
formes identifiées (`Target`, `Block`, `Southern`, `Rollins`) tout en autorisant
leurs noms juridiques complets, et abandonne l'hypothèse qu'un acronyme entre
parenthèses est nécessairement un ticker. Les alertes passent de 45 à huit sans
modifier les classifications. La relecture de ces huit cas n'effectue que des
ajouts ; la composition reste une responsabilité déterministe du lot 3.

## Stratégie modèle initiale

Le prompt actif `entity-sentiment-v5-rcorcf` suit Rôle, Contexte, Objectif,
Résultat, Contraintes, Format et contient douze exemples fictifs vérifiés par les
tests. Le pilote API v4 récupère la mention Waymo/Alphabet manquante en v2 ;
un test ultérieur sur dix autres articles révèle encore deux omissions de
mentions secondaires et un sentiment à arbitrer. Les décisions et
la signification des versions sont dans [PROMPT_DESIGN.md](docs/PROMPT_DESIGN.md).

Un article complet par requête, accompagné de la liste canonique des entreprises.
Le modèle doit considérer toutes les entreprises mentionnées, y compris les acteurs
neutres. Demander des objets structurés : ticker, label et extrait justificatif.
Utiliser Responses avec `text.format` en JSON Schema strict, `reasoning.effort=low`,
`store=false`, `service_tier=default` et 4 096 tokens de sortie maximum par défaut.
Ces possibilités ont été vérifiées dans la [fiche du modèle](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
et le [guide Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
La compatibilité de la clé a été confirmée le 13 octobre. En cas d'indisponibilité, arrêter sans
substitution. Le client impose l'endpoint OpenAI et refuse les redirections HTTP.

Le contexte inclut l'implication pour la valeur à la date de publication, sans
prédiction de rendement. Les articles peuvent favoriser une entreprise et en
défavoriser une autre. Le code ne déduit pas un sentiment global unique.

Une preuve doit correspondre au texte normalisé ; elle améliore la traçabilité
mais ne garantit ni le bon parent d'une marque ni l'exhaustivité. Un préfiltre et
des alias supplémentaires ne seront ajoutés que si une évaluation en justifie le
gain sans perte de rappel. Pas de nouvelles ou de cours externes.

## Reproductibilité et erreurs

La clé de cache SHA-256 inclut contenu normalisé, date, univers canonique, version
de normalisation, prompt, schéma, modèle et paramètres. L'identifiant de l'article
est exclu : deux identifiants au contenu et à la date identiques peuvent partager
une analyse, tout en restant deux articles distincts pour le calcul. Le modèle,
la version du prompt, les réservations et les empreintes sont consignés.
Une réponse relue du cache est revalidée ; un cache corrompu fait échouer le run.
Les sorties validées seront triées et l'agrégation utilisera un ordre stable.
Un nouvel appel API peut varier ; le cache permet de rejouer un résultat validé.

Par défaut, deux tentatives au maximum par article (configurable de 1 à 3).
Une réponse structurée invalide peut être redemandée ; chaque tentative est
comptabilisée. Une erreur 429 explicitement `rate_limit_exceeded` permet une reprise
avec attente bornée, sans effacer la réservation de coût inconnu. Une interruption
réseau, une erreur de clé/quota ou une consommation non vérifiable arrête le run.
Il n'y a pas de reprise implicite du transport. Une réponse
invalide n'est ni ignorée ni convertie en neutralité. Une erreur définitive fait
échouer le run avec diagnostic et conserve le cache réutilisable. Les exports
finaux ne sont publiés dans le dossier de run qu'après traitement complet.
Les erreurs de validation consignent un motif fixe dans `validation_error`,
sans recopier le contenu de la réponse rejetée.

## Usage et coût

Suivre chaque tentative : article, statut, modèle, identifiant de requête lorsque
disponible, tokens d'entrée, lecture et écriture du cache fournisseur, tokens de
sortie (raisonnement inclus) et durée.
La réponse de l'API fait foi pour les tokens ; les valeurs manquantes restent
inconnues. Le cache local et le cache de tokens du fournisseur sont distincts.

Calcul en USD avec tarifs standard de contexte court, vérifiés le 12 octobre
2026 : entrée ordinaire 2 USD/million, lecture cache 0,20, écriture cache 2,50,
sortie 12. Sources : [modèle](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
et [catégories du cache fournisseur](https://developers.openai.com/api/docs/guides/prompt-caching).

```text
coût = ((entrée - lecture_cache - écriture_cache) × tarif_entrée
        + lecture_cache × tarif_lecture_cache
        + écriture_cache × tarif_écriture_cache
        + sortie × tarif_sortie) / 1_000_000
```

Les deux catégories de cache sont distinctes et incluses dans l'entrée totale.
Un champ d'usage manquant, un modèle ou un niveau de service inattendu provoque
un arrêt avec coût inconnu, jamais zéro par défaut.
`run_report.json` et la commande `usage` agrègent ces rapports : appels, reprises,
tokens et coût par catégorie, coût par étape et par article. Le run réel
`run-final-v1` coûte 3,0187697 USD, soit 0,0302 USD par article, dont 2,589 USD
(86 %) d'écriture au cache fournisseur. Chaque requête répète environ 14 000 tokens
de consignes et d'univers, mais seuls 36 % sont relus depuis le cache ; le reste est
écrit au tarif majoré de 2,50 USD par million. C'est le principal levier d'une
optimisation de coût (préfiltrage de l'univers ou meilleure réutilisation du cache).

Coût/article du run complet = coût total de ses tentatives / nombre d'articles
traités (100 pour les données fournies). Rapporter séparément appels, reprises,
hits de cache local et run initial sans cache. Ne pas présenter un replay gratuit
comme le coût de classification initial. Comparer au relevé fournisseur si disponible.

Avant chaque appel, réserver une estimation prudente incluant entrée et sortie
maximale ; bloquer si le budget ne permet pas cet appel. L'estimation d'entrée
utilise le nombre d'octets UTF-8 de la requête plus 4 096, sans prétendre être un
compteur de tokens exact. Au-delà de 200 000 tokens estimés, refuser la requête
pour rester dans le contexte court. La réservation est écrite avant l'appel puis
remplacée par le coût mesuré ; un dépassement stoppe les appels suivants. Ce
contrôle local ne garantit pas un plafond absolu côté fournisseur. Après une
interruption, la réservation persiste et `total_cost_usd` reste nul au sens JSON
(`null`), distinct de zéro dollar. Le cap de la clé est une protection supplémentaire.

## Sécurité et proportion

Clé en variable d'environnement, caches et artefacts ignorés, logs sans secrets.
Depuis le 13 octobre, `config.py` charge aussi `OPENAI_API_KEY` depuis `.env` dans
le dossier courant, seulement avant une classification ou relecture avec budget.
Une variable existante non vide est prioritaire. Chargeur limité à cette clé,
sans recherche dans les dossiers parents, interpolation ou exécution du contenu.
Erreurs sans valeur secrète ; `.env` ignoré, `.env.example` vide versionnable.
Texte des articles isolé des instructions, sans outils accessibles au modèle.
Pas de télémétrie ou d'envoi externe autre que l'API exigée lors d'un run autorisé.
Ne pas ouvrir de services réseau. Préserver les sources et refuser les collisions
entre chemins d'entrée et de sortie. Les tests utilisent des réponses simulées.
