# Revue des analyses — échantillon initial

Statut : N001, N002 et N027 analysés par API et relus par l'agent le 13 octobre ;
pas de validation humaine indépendante. Ce document n'est pas un jeu de vérité terrain et ne
permet pas de revendiquer un score de précision. Les faits des articles sont
traités dans le cadre du sujet, sans vérification ou enrichissement externe.

## Sélection

| Article | Point à vérifier en lisant le texte entier |
| --- | --- |
| N001 | Distinguer la société évaluée de la banque émettant une recommandation ; conserver les mentions neutres |
| N002 | Classifier séparément chaque société et conserver uniquement l'univers fourni |
| N003 | Reconnaître les graphies Unicode ressemblantes avec le contexte des produits ; distinguer nouvelles et rappels historiques |
| N027 | Vérifier les mentions après retrait des U+200B, sans altérer les sources |
| N029 | Le sujet principal peut être hors univers ; un client pilote n'hérite pas automatiquement du sentiment de la levée de fonds |
| N070 | Rattacher produit et filiale au parent explicite ; examiner aussi les mentions incidentes, dont le nom d'une conférence |
| N077 | Évaluer séparément les concurrents, rattacher les marques et examiner la source médiatique ; éviter les doubles classes |
| N096 | Une entreprise hors univers ne devient pas éligible parce qu'un investisseur ou partenaire est connu ; examiner la possibilité d'une liste vide |

Premier essai technique exécuté : `N001 N002 N027`. Étendre ensuite à des articles
distincts ci-dessus selon le budget, après consolidation des omissions observées.

## Revue assistée du pilote — 13 octobre 2026

Relecteur : agent Codex, après lecture des prédictions et du texte complet.
Il ne s'agit donc pas d'annotations indépendantes ni d'un benchmark.

| Article / ticker | Attendu selon la revue | v1 (pilot-002) | v2 (pilot-003, retenu) | Motif |
| --- | --- | --- | --- | --- |
| N001 / FIS | negative | negative | negative | Dégradation et baisse des prévisions |
| N001 / FISV | negative | negative | negative | Problèmes de prévisions mentionnés pour Fiserv |
| N001 / MS, WFC | neutral | neutral | neutral | Banques émettant les recommandations, sans impact propre établi |
| N002 / COIN, XYZ | positive | positive | positive | Relèvement des objectifs avec recommandation favorable |
| N002 / GS | neutral | omis | neutral | Goldman Sachs émet la recommandation ; mention éligible |
| N027 / TSLA | negative | negative | negative | Chute du titre et enquête |
| N027 / GOOGL | neutral | omis | omis | Waymo sert de comparaison de flotte ; lien au parent inféré, absent du CSV |

Microstrategy et Circle sont hors de l'univers fourni ; leur omission n'est pas
une erreur. La mention de l'indice Nasdaq dans N001 ne suffit pas à identifier
l'entreprise opératrice NDAQ. Le rattachement Waymo/Alphabet est une inférence de
connaissance du modèle/agent à faire valider en revue ; aucune source métier
externe n'a été consultée.

Le prompt v2 demande un inventaire de chaque paragraphe avant l'attribution des
labels, notamment banques, sources et comparaisons. Une variante v3 clarifiant
le recours aux liens de filiation connus et utilisant `reasoning.effort=medium`
a été testée dans `pilot-004` : GS et GOOGL y manquent. Cette variante n'est pas
retenue. Ni les résultats ni les caches n'ont été corrigés manuellement.

Limite actuelle : la complétude des extractions n'est pas garantie par le schéma
JSON ni par une instruction supplémentaire. Avant un run complet, envisager une
vérification dédiée des mentions oubliées et l'évaluer sur les autres articles
de revue, sans se limiter aux trois cas ayant servi à ajuster le prompt.

Refonte ultérieure demandée par l'utilisateur : v4 RCORCF et dix exemples
pédagogiques. Le résultat API v4 est maintenant dans `output/pilot-005`. N027 est désormais
un cas de développement enseigné explicitement via un exemple fictif Waymo ;
ne pas le compter comme évaluation indépendante de la nouvelle version.

## Retest RCORCF v4 — 13 octobre 2026

| Article | Classifications obtenues |
| --- | --- |
| N001 | FIS negative ; FISV negative ; MS neutral ; WFC neutral |
| N002 | COIN positive ; GS neutral ; XYZ positive |
| N027 | GOOGL neutral ; TSLA negative |

Les neuf paires correspondent à notre revue assistée de ces trois articles.
Par rapport à v2, GOOGL est ajouté via l'extrait de comparaison avec Waymo ;
aucun autre ticker ou label ne change. Goldman Sachs, récupéré par v2 et perdu
dans l'essai v3, est bien conservé. Les extraits passent le contrôle de présence
exacte dans le texte normalisé. Aucun résultat n'a été retouché.

Trois appels, aucune reprise, aucun cache local utilisé : 0,0888659 USD,
40 884 tokens d'entrée et 677 de sortie. Ce petit ensemble déjà utilisé pour
concevoir le prompt ne démontre pas la qualité sur le reste des articles.

## Méthode

Extension exécutée sur dix autres articles, avec attentes de l'agent consignées
avant les appels : [REVIEW_10.md](REVIEW_10.md). Les désaccords y sont conservés ;
il ne s'agit toujours pas d'annotations humaines indépendantes.

1. Avant de consulter la prédiction, lire le titre et le corps normalisés. Relever
   toutes les entreprises identifiables, leur ticker canonique dans le CSV, leur
   rôle, le label attendu et l'extrait justificatif. Noter les cas incertains.
2. Comparer aux objets de `classifications.json` : omissions, ajouts injustifiés,
   parent incorrect, sentiment attribué à la mauvaise entreprise, ancien fait
   dominant abusivement la nouvelle information, neutralité oubliée.
3. Consigner les décisions dans une table de revue : `article_id`, `ticker`,
   `expected_label`, `predicted_label`, `error_type`, `rationale`, `reviewer`.
   Ne pas modifier directement les résultats produits par la pipeline.
4. Corriger le prompt ou le code pour une erreur récurrente ; changer sa version,
   régénérer sous budget et conserver la trace du désaccord. Réserver quelques
   autres articles à une vérification après correction pour limiter le surajustement.

Quand les annotations existent, mesurer séparément précision/rappel des paires
article-ticker et exactitude des labels sur les paires correctement détectées.
Indiquer le nombre de cas, les arbitrages et la taille limitée de l'échantillon.
La présence d'un extrait exact valide la traçabilité textuelle, pas la justesse du
label, du lien marque-parent ou l'exhaustivité des entreprises trouvées.
