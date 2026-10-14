# Test de classification sur les 100 articles — 13 octobre 2026

## Périmètre

Exécution demandée avant l'agrégation. Sources inchangées : `news.json` et
`sp500.csv`. Modèle `gpt-5.6-terra`, prompt `entity-sentiment-v4-rcorcf`, effort
low, sortie structurée et validation habituelle. Budget disponible au départ :
3,8541396 USD, après conservation de la réservation inconnue antérieure.

La première passe se trouve dans `output/full-100-v4`. Elle contient les 100
articles et reste l'artefact complet de référence. La relecture ciblée se trouve
dans `output/full-100-targeted-review` et contient uniquement les huit articles
signalés. Aucune fusion ou correction manuelle des classifications n'a été faite.

## Première passe

- 100 articles terminés, 87 appels et 13 résultats repris d'un cache compatible.
- Aucune reprise, aucun coût inconnu dans ce run.
- 217 paires article/ticker : 70 positive, 93 neutral et 54 negative.
- 11 articles avec une liste vide validée.
- 1 186 925 tokens d'entrée, dont 401 276 lus et 785 388 écrits au cache
  fournisseur ; 16 733 tokens de sortie.
- Coût du run : **2,2450432 USD**. Il ne représente pas le coût initial des 13
  résultats locaux réutilisés, déjà comptabilisé dans les essais précédents.

## Ajustement du contrôle déterministe

La première mesure a produit 45 alertes. La majorité était fausse : les mots
ordinaires `target`, `block` et `southern`, le nom de personne Rollins, ainsi que
les acronymes entre parenthèses `(MA)` et `(CMS)`, étaient confondus avec des
entreprises ou tickers.

La correction `entity-coverage-v3` et le registre `entity-aliases-v2` :

- excluent les formes courtes ambiguës tout en conservant les noms juridiques
  complets et les tickers explicitement balisés ;
- ne considèrent plus toute parenthèse en majuscules comme un ticker ;
- conservent les alias certains et l'ambiguïté Everpure sans ajout automatique.

Après correction, huit articles seulement sont signalés : N012, N013, N038,
N070, N076, N077, N084 et N091. Les 75 tests hors réseau passent.

## Relecture ciblée

Huit appels, aucune reprise ni cache local, pour **0,2281222 USD**. 115 346 tokens
d'entrée, dont 34 916 lus et 80 406 écrits au cache fournisseur ; 1 673 de sortie.

| Article | Ajouts proposés | Motif |
| --- | --- | --- |
| N012 | STT neutral | marque SPDR |
| N013 | NWSA neutral ; WBD neutral | Wall Street Journal ; CNN retrouvé par la relecture |
| N038 | SBUX neutral | Starbucks comme lieu incident |
| N070 | JPM neutral | nom de la conférence JP Morgan |
| N076 | BLK neutral | marque iShares |
| N077 | NWSA neutral | Wall Street Journal |
| N084 | aucun | P, PNR et CMG déjà correctement distingués |
| N091 | IVZ neutral | Invesco QQQ Trust |

Aucune suppression ni modification de label. Toutes les alertes fiables sont
couvertes. N084 conserve un motif d'ambiguïté par conception, mais la proposition
contient bien P neutral et PNR negative avec des preuves distinctes.

Si les huit propositions remplaçaient leurs huit lignes initiales, le résultat
aurait 225 paires : 70 positive, 101 neutral et 54 negative. Cette composition
est seulement vérifiée en mémoire ; elle n'est pas écrite avant l'implémentation
d'une composition explicite et testée au lot suivant.

## Contrôles, coût et limites

Les deux manifestes sont `completed`. Les 100 identifiants, 225 paires composées,
preuves, tickers, labels, clés des huit requêtes, empreintes des sources, du registre
et de la première classification ont été revalidés. Les sources sont intactes ;
clé, caches et sorties sont ignorés par Git.

Coût additionnel de ce test : **2,4731654 USD**. Coût connu cumulé du projet :
**3,4452688 USD** ; réservation inconnue conservée : **0,173757 USD** ; solde
prudent du budget de 5 USD : **1,3809742 USD**.

Le succès structurel ne prouve pas la justesse sémantique des 100 articles. Seul
le petit jeu documenté a reçu une revue humaine assistée détaillée ; NFLX/N077
reste notamment un sentiment mixte discuté. La relecture utilise le même modèle,
donc elle n'est pas une vérité terrain indépendante.

## Dernière passe v5 après la revue

Le prompt `entity-sentiment-v5-rcorcf` ajoute une règle et deux exemples fictifs
pour distinguer une information centrale d'une performance historique ou d'un
faible mouvement de pair cité en comparaison. Il traite aussi séparément les
effets d'un accord pour chacune de ses parties. Le registre `entity-aliases-v3`
ajoute CNN → WBD. Ces changements sont couverts par les tests hors réseau.

Le résultat complet cohérent est dans `output/full-100-v5-final`. Son manifeste
est `completed` : 100 articles, 90 résultats repris du cache compatible et dix
appels dans le run final. Les 220 paires se répartissent en 62 positive,
105 neutral et 53 negative ; 11 articles restent sans entreprise éligible.
Les preuves, tickers, labels, identifiants et empreintes des sources sont valides.

Par rapport à la composition conceptuelle v4 + revue ciblée, 29 articles changent :
sept paires sont ajoutées, douze retirées et 23 labels changent. Les changements
recherchés sont obtenus : NVDA/N069, GOOGL-NFLX-RDDT/N091 et AAPL/N095 deviennent
neutral. QCOM/N095 reste positive. GS et MS/N047 deviennent aussi neutral comme
mouvements secondaires de marché.

La passe n'est cependant pas meilleure dans son ensemble. Elle omet notamment
des sources, marques ou filiales neutres ; le contrôle déterministe signale STT,
NWSA, WBD, SBUX et BLK dans huit articles. PCAR/N078 et CMCSA/N082 disparaissent
également sans être couverts par ces alias. Deux faux `XYZ` sont ajoutés dans
N023 et N100 parce que le réseau social X est confondu avec Block. BAC/N092 reçoit
à tort `negative` pour avoir publié une dégradation sur Nike, en contradiction
avec la règle explicite sur les banques analystes. NVDA/N076 reçoit `positive`
à partir d'anciens résultats malgré le sujet central défavorable des ventes
d'initié. D'autres désaccords, comme ADBE/N039, restent discutables.

Le coût connu des exécutions v5 est **2,6571634 USD**. Le coût connu cumulé du
projet est **6,1024322 USD**. Deux réservations inconnues totalisent 0,349960 USD,
soit un engagement prudent de **6,4523922 USD** sur le plafond de 10 USD.

Conclusion : conserver la règle v5, mais ne pas promouvoir son JSON brut. Aucun
résultat n'a été retouché manuellement.

## Composition et garde-fous déterministes

La commande `compose` a matérialisé la composition v4 + revue ciblée dans
`output/composition-audit-v3/`. Elle vérifie les empreintes des artefacts, refuse
une revue incomplète, conserve la provenance des huit articles remplacés et
compare la candidate v5 sans la promouvoir. Le résultat contient 100 articles et
225 paires, mais `ready_for_scoring` vaut `false`.

Sept alertes bloquent la composition : CMCSA manque dans N030, N047 et N061 ;
CMCSA et PSKY manquent dans N048 ; NWSA manque dans N066 ; XOM/N100 repose sur
le faux rapprochement entre SpaceX et Exxon Mobil. Ces cas correspondent à des
alias explicites nouvellement versionnés ou à un alias interdit, pas à une simple
variation arbitraire du modèle.

La candidate v5 comporte quinze alertes bloquantes : omissions STT/N012,
NWSA-WBD/N013, SBUX/N038, BLK/N043, CMCSA/N047, STT/N049, CMCSA/N061,
BLK/N076, PCAR/N078, CMCSA/N082, STT/N089 et NWSA/N097, plus les faux XYZ/N023
et XYZ/N100. Elle diffère de la composition sur 29 articles. Le contrôle de rôle
signale aussi BAC/N092 comme possible transfert de sentiment depuis Nike ; ce
signal reste consultatif pour éviter de transformer une heuristique lexicale en
décision métier.

Le registre est `entity-aliases-v5` : CNBC et NBC News sont rattachés à CMCSA,
CBS et CBS News à PSKY, Barron's à NWSA et Kenworth à PCAR. `X → XYZ` et
`SpaceX → XOM` sont interdits. Les contrôles ne modifient aucune classification :
ils empêchent seulement une composition douteuse d'entrer dans le calcul.

## Résolution des blocages

Une première relecture commune des six articles a ajouté toutes les sources et
retiré XOM/N100, mais elle a aussi changé trois labels et supprimé SCHW/N066. Ce
lot a été rejeté. Le mode `additions-only` a ensuite rendu les invariants
exécutables : toute suppression ou modification d'un label existant invalide la
réponse. Quatre réponses conformes ont été conservées depuis le cache ; N066 a
nécessité deux tentatives avant de préserver SCHW tout en ajoutant NWSA. N100 a
été isolé et sa réponse validée retire uniquement XOM.

La composition retenue se trouve dans `output/composition-final-v3/`. Elle couvre
100 articles et 230 paires : 70 positive, 106 neutral et 54 negative ; 11 articles
restent sans entité. Par rapport à la composition de 225 paires, elle ajoute
CMCSA/N030, CMCSA/N047, CMCSA-PSKY/N048, CMCSA/N061 et NWSA/N066, tous neutral,
et retire XOM/N100. Aucun label existant ne change. Le rapport compte zéro alerte
bloquante, 60 alertes consultatives et indique `ready_for_scoring=true`.

Cette phase ajoute **0,3314652 USD** de coût connu. Une tentative N100 interrompue
conserve en plus une réservation prudente de 0,179378 USD. Le cumul projet devient
6,4338974 USD connus et 0,529338 USD inconnus/réservés, soit 6,9632354 USD engagés
sur 10 USD. Les 86 tests hors réseau passent ; la compilation Python et les
empreintes identiques des compositions finales v1/v2 confirment que le dernier
durcissement n'a pas modifié les 230 classifications.

## Export temporel

`output/final-results-v1/` est généré sans réseau depuis la composition approuvée.
`entities.csv` contient 230 lignes triées par `(id, ticker)` et `scores.csv`
111 lignes triées par ticker, dont 26 valeurs nulles. Le calcul utilise la
référence du 29 septembre 2026 à minuit à New York, convertit les instants en UTC,
applique la demi-vie de sept jours et additionne avec `math.fsum`.

Le manifeste final est `completed`, lie les empreintes des données, de la
composition et des deux CSV, et refuse toute composition modifiée ou non prête.
Les scores positifs les plus élevés commencent par GOOGL, AMD, UAL, DAL et QCOM ;
les plus négatifs commencent par NKE, BX, BA, TSLA et CMCSA. Ces valeurs sont des
agrégats du jeu fourni, pas des recommandations d'investissement.

## Évaluation humaine à compléter

Une comparaison directe entre la composition finale et v5 produit 39 décisions
différentes sur 27 articles. Le dossier `review/human-evaluation-v1/` contient la
liste complète et un échantillon de dix cas variés avec le texte intégral, les
deux labels et leurs preuves. Les annotations sont volontairement vides : aucune
version n'est utilisée comme vérité de référence.

Après remplissage de `human_decision`, la commande `evaluate` mesurera séparément
l'accord de la composition finale et de v5. Les CSV de `final-results-v1` doivent
être considérés comme provisoires sur le plan sémantique jusqu'à cet arbitrage,
même si leurs schémas, calculs et empreintes sont valides.
