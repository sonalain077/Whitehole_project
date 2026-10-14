# Test RCORCF sur dix autres articles — 13 octobre 2026

## Sélection et attentes avant les appels

Prompt figé : `entity-sentiment-v4-rcorcf`, modèle `gpt-5.6-terra`, effort low,
une tentative maximum par article. Aucun de ces dix articles n'a été traité dans
les pilotes précédents. Sélection ciblée pour varier les difficultés, non aléatoire.
Certains thèmes ressemblent aux exemples du prompt, notamment le client pilote
Microsoft ; ce n'est pas un test entièrement indépendant des choix de conception.

Les attentes ci-dessous sont établies par l'agent après lecture des textes et du
référentiel, AVANT de demander les prédictions. Ce sont des annotations provisoires
à faire relire par un humain, pas une vérité terrain certifiée. Les faits du jeu
sont traités comme données du sujet, sans vérification externe.

| Article | Attentes provisoires | Point de contrôle |
| --- | --- | --- |
| N003 | F negative ; TSLA negative | Homoglyphes de Tesla et TSLA, contexte Cybertruck ; Rivian et Reuters hors univers |
| N029 | MSFT neutral | Pilote sans engagement commercial ; startup et TSMC hors univers |
| N054 | DAL, HD, KO, UPS neutral | Entreprises citées sans perturbation opérationnelle établie malgré le titre négatif |
| N063 | AAPL, GOOGL neutral | Retrait d'application, plateformes explicitement non impliquées dans la fuite ; banques non nommées exclues |
| N064 | COIN positive ; AAPL, MSFT, NVDA, TSLA, NWSA neutral | Opportunité de nouveaux contrats pour Coinbase, sous-jacents sans impact propre ; WSJ comme source |
| N070 | JNJ positive ; JPM neutral | Produit et filiale rattachés à J&J, conférence JP Morgan incidente |
| N077 | GOOGL positive ou neutral ; NFLX positive ou neutral ; NWSA neutral | Nouvelles initiatives favorables face à une concurrence accrue ; sentiment net ambigu à arbitrer |
| N084 | PNR negative ; CMG neutral ; P neutral | Everpure filtration appartient à Pentair ; homonyme P distinct, baisse temporaire puis récupération ; client sans fermeture |
| N096 | Aucune entité éligible | Ne pas ajouter les investisseurs ou partenaires non nommés d'OpenAI/Anthropic |
| N097 | BA negative ; GE negative ou neutral ; RTX, LMT, NWSA, BLK, STT neutral | Effet principal Boeing ; petit mouvement GE à arbitrer ; WSJ et marques de fonds iShares/SPDR |

Les liens WSJ → News Corp, iShares → BlackRock et SPDR → State Street sont des
inférences d'identité connues par l'agent, pas des relations fournies par le CSV.
Leur inclusion et la mention de JPM dans un nom de conférence méritent une revue
humaine explicite. Les alternatives de sentiment sont déclarées à l'avance pour
ne pas transformer après coup toute prédiction en résultat correct.

Trente paires article/ticker sont proposées au total, sous réserve de ces
arbitrages. Une liste vide est attendue pour N096. Comparer séparément la présence
des entreprises, les sentiments et l'exactitude textuelle des preuves. Ne pas
modifier les sorties pour les faire correspondre aux attentes.

## Résultats

Run complet : `output/review-010-resume/classifications.json`.

| Article | Résultat obtenu | Comparaison aux attentes préalables |
| --- | --- | --- |
| N003 | F negative ; TSLA negative | Conforme ; le nom Tesla en caractères ressemblants est reconnu |
| N029 | MSFT neutral | Conforme ; aucun bénéfice attribué au simple client pilote |
| N054 | DAL, HD, KO, UPS neutral | Conforme ; aucune contamination par le ton négatif du fait divers |
| N063 | AAPL, GOOGL neutral | Conforme ; plateformes sans implication propre dans la fuite |
| N064 | COIN positive ; AAPL, MSFT, NVDA, NWSA, TSLA neutral | Conforme après reprise technique ; WSJ rattaché à News Corp |
| N070 | JNJ positive | JPM absent malgré « JP Morgan Healthcare Conference » ; omission au regard de notre règle de mentions incidentes, à confirmer humainement |
| N077 | GOOGL neutral ; NFLX negative | NWSA absent malgré WSJ ; label Netflix en désaccord avec les alternatives préalables, à arbitrer |
| N084 | CMG neutral ; P neutral ; PNR negative | Conforme ; les deux Everpure sont distingués et le client n'hérite pas du rappel |
| N096 | Liste vide | Conforme ; aucun investisseur ou partenaire non nommé ajouté |
| N097 | BA negative ; GE, RTX, LMT, NWSA, BLK, STT neutral | Conforme aux alternatives préalables, sous réserve des inférences de marques et du label GE |

Vingt-huit paires produites sur les trente proposées dans la revue provisoire,
sans paire supplémentaire. Deux omissions et un désaccord de sentiment sont
signalés. Huit articles correspondent entièrement aux attentes ou alternatives
déclarées avant les appels. Cela mesure l'accord avec CETTE revue de l'agent,
pas une précision de production certifiée ni une validation humaine indépendante.

Pour Netflix, la preuve choisie mentionne la baisse d'engagement, alors que le
texte traite aussi d'acquisition de contenus pour la compenser. Le label négatif
peut refléter cette difficulté ; il faut arbitrer l'implication nette sans changer
les attentes après coup pour cacher le désaccord. L'omission de News Corp est
distincte de cet arbitrage : WSJ est explicitement cité dans l'article.

## Exécution et coût

Le premier run `output/review-010` s'arrête sur N064 après quatre résultats valides
et une réponse rejetée. Son motif précis n'était pas conservé par le journal
initial et la réponse invalide n'a pas été sauvegardée : ne pas inventer la cause.
Ajout d'un diagnostic fixe `validation_error` aux erreurs futures, sans texte de
réponse ni clé ; les tests de non-divulgation et la suite complète passent (63).
Le prompt, le schéma et les validations restent inchangés.

La reprise dans un nouveau dossier réutilise les quatre résultats en cache et
termine les six autres sans nouvel échec. N064 a donc nécessité deux appels au
total, tous comptabilisés. Les résultats du modèle n'ont pas été retouchés.

| Exécution | Appels | Cache local | Coût USD |
| --- | --- | --- | --- |
| review-010, interrompu | 5 | 0 | 0,1322405 |
| review-010-resume, terminé | 6 | 4 | 0,1469120 |
| Total du test sur dix articles | 11 | 4 relectures | 0,2791525 |

Tokens cumulés : 149 790 en entrée, dont 60 340 en lecture cache et 89 417 en
écriture cache fournisseur ; 3 623 en sortie. Coût par article du test complet,
réponse rejetée comprise : 0,02791525 USD. Le coût de la seule reprise ne doit pas
être présenté comme celui des dix classifications initiales.

Coût connu cumulé du projet : 0,6048610 USD ; réservation inconnue conservée du
premier échec réseau : 0,173757 USD ; solde prudent des 5 USD : 4,2213820 USD.

Contrôles : dix identifiants distincts, manifeste terminé, bonne version et bonnes
empreintes de requêtes, revalidation des 28 entrées et preuves exactes, deux
sources intactes. Les données, sorties et caches n'ont pas été modifiés manuellement.

Suite proposée : revue humaine des cas signalés, puis amélioration ciblée du
contrôle des mentions secondaires. Ne pas conclure que la seule présence des
exemples RCORCF garantit l'exhaustivité sur les 100 articles.

## Seconde passe expérimentale — 13 octobre 2026

Exécution `output/verification-010`, prompt `entity-review-v1` ajouté au RCORCF v4,
même modèle et effort low. La proposition initiale et les indices lexicaux sont
transmis, mais pas les attentes de cette revue. Aucun résultat initial modifié.

| Cas | Première passe | Seconde passe | Bilan provisoire |
| --- | --- | --- | --- |
| N077, News Corp | NWSA absent | NWSA neutral, extrait citant The Wall Street Journal | Omission corrigée |
| N070, conférence | JPM absent | JPM toujours absent | Omission maintenue, à arbitrer humainement |
| N084, Everpure stockage | P neutral | P supprimé | Régression : l'entreprise distincte est explicitement nommée ; contrôle lexical P non couvert |
| N077, Netflix | NFLX negative | NFLX negative | Désaccord de sentiment inchangé |

Les huit autres articles conservent les mêmes tickers et labels. Total toujours
28 paires : un ajout, une suppression, aucun changement de sentiment. Deux paires
manquent par rapport aux trente attendues provisoirement (JPM et désormais P).
Sept articles correspondent entièrement aux attentes initiales, contre huit
avant relecture. Cela reste un accord avec les annotations de l'agent, pas un
score de précision établi sur un jeu validé humainement.

Les indices lexicaux signalent aussi NDAQ dans N003 et N070, à cause de Nasdaq :
ces alertes ne justifient pas un ajout automatique de l'entreprise. Ils ne
repèrent ni la variante JP Morgan ni la marque WSJ avec les seuls noms du CSV.
Leur intérêt ici est de rendre visible la suppression de P, pas de garantir
l'exhaustivité ou la justesse du rattachement des marques.

**Décision :** conserver cette sortie comme proposition à examiner. La première
passe reste le point de comparaison ; aucune fusion ni correction manuelle.
Avant de retenir une nouvelle stratégie, arbitrer les cas humains et vérifier
les régressions sur les mêmes critères, puis sur des articles distincts.

**Exécution :** dix appels, zéro reprise, zéro cache local ; 141 562 tokens
d'entrée (44 496 lecture cache, 97 036 écriture cache), 1 911 de sortie.
Coût additionnel **0,2744812 USD** ; cumul connu **0,8793422 USD**, réservation
inconnue conservée **0,173757 USD**, solde prudent **3,9469008 USD**.
71 tests hors réseau passent. Dix requêtes et 28 paires revalidées, empreintes des
sources et du résultat initial inchangées ; `.env`, cache et sorties ignorés par Git.

## Relecture ciblée v2 — 13 octobre 2026

Après gel du registre `entity-aliases-v1` et des règles `entity-coverage-v2`, le
dry-run sélectionne uniquement N070, N077 et N084. Le mode ciblé n'a reçu ni les
attentes de ce document ni les corrections attendues ; il reçoit l'article, le
référentiel, la première proposition et les indices déterministes.

| Cas | Résultat v2 ciblé | Arbitrage |
| --- | --- | --- |
| N070 | JPM neutral ajouté ; JNJ positive conservé | Conforme |
| N077 | NWSA neutral ajouté ; GOOGL neutral conservé | Couverture conforme |
| N077 | NFLX reste negative | Désaccord maintenu avec notre préférence neutral ; cas réellement mixte |
| N084 | P neutral, PNR negative et CMG neutral conservés | Régression v1 corrigée |
| Nasdaq | Aucun NDAQ ajouté | Faux positif supprimé |

La couverture des entités atteint les trente paires attendues provisoirement une
fois les trois propositions ciblées appliquées aux sept résultats inchangés.
Cette mesure dépend toujours de l'annotation de l'agent. Le résultat v2 reste un
artefact séparé ; aucune fusion manuelle ou automatique n'a été effectuée.

Exécution `output/targeted-review-003` : trois appels, aucune reprise ni cache
local, 43 025 tokens d'entrée (9 976 en lecture et 33 040 en écriture cache),
679 tokens de sortie, **0,0927612 USD**. C'est environ 66 % moins cher que la
relecture générale des dix articles (0,2744812 USD), tout en corrigeant sa
régression observée. Ce rapport ne prédit pas la proportion d'alertes sur 100
articles. Cumul connu **0,9721034 USD**, réservation inconnue **0,173757 USD**,
solde prudent **3,8541396 USD**.

Les 74 tests hors réseau passent. Les trois réponses, preuves, clés de requête,
empreintes du registre, de la classification initiale et des deux sources ont été
revalidées. La prochaine itération peut porter sur l'agrégation et les CSV, en
conservant le désaccord NFLX dans les limites de qualité.
