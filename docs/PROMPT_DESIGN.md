# Prompt RCORCF et versions

État au 13 octobre 2026 : `entity-sentiment-v5-rcorcf` est le prompt actif. Il est
testé hors réseau et exécuté sur les 100 articles. La version v4 a également été
exécutée sur les 100 articles ; le pilote
N001, N002 et N027 reste dans `output/pilot-005`. Goldman Sachs reste neutre et Alphabet
via Waymo est maintenant identifié en neutre, sans autre variation de label ou
de couverture par rapport à v2 (`output/pilot-003`). Coût v4 : 0,0888659 USD pour
trois appels, contre 0,0787458 USD pour v2. Cette comparaison inclut les différences
d'utilisation du cache fournisseur ; elle ne mesure pas un surcoût fixe du prompt.

Un [test sur dix autres articles](REVIEW_10.md) a ensuite produit 28 paires, avec
deux omissions et un sentiment en désaccord avec la revue préalable de l'agent.
Le prompt n'a pas été modifié pour ce test ; l'exhaustivité reste à améliorer.

## Relecture expérimentale

`review.py` définit `REVIEW_VERSION = entity-review-v1`. Il conserve le prompt
RCORCF v4 et ajoute des consignes d'inventaire indépendant, de vérification des
mentions secondaires et de conservation des entités justifiées. Un troisième
message de données contient les propositions et les indices lexicaux, jamais
les annotations attendues de `REVIEW_10.md`. Le schéma, le modèle et l'effort
de raisonnement ne changent pas.

`COVERAGE_VERSION = explicit-name-ticker-v1` identifie les règles déterministes
de détection des indices. `NORMALIZATION_VERSION` reste inchangée : aucun nouveau
nettoyage du texte. La requête complète, donc les instructions, les indices et
la proposition initiale, entre dans la clé de cache. Le manifeste de relecture
porte `entity-review-v1`. Une version sert à tracer une recette, pas à certifier
qu'elle est meilleure. L'essai dans `output/verification-010` corrige un oubli
mais en introduit un autre ; il ne justifie pas une adoption automatique.

`entity-review-v2-targeted` ajoute la distinction entre indices fiables et ambigus,
ainsi qu'une règle de conservation forte pour une entreprise explicitement nommée
avec ticker et preuve. `entity-coverage-v2` génère les variantes juridiques depuis
le CSV et charge `entity-aliases-v1`. Un indice fiable peut déclencher une revue ;
un indice ambigu déclenche une revue sans imposer tous ses candidats. Les données
du registre, la proposition et l'article participent à la requête et donc au cache ;
le fichier de registre est aussi empreint dans le manifeste.

Le test ciblé sur N070/N077/N084 ajoute JPM et NWSA et conserve P. Il maintient
NFLX negative malgré l'alternative neutral de la revue préalable. Cette version
améliore la couverture du petit échantillon, sans prouver sa généralisation.

Sur les 100 articles, la politique lexicale devient `entity-coverage-v3` avec
`entity-aliases-v2`. Le prompt de relecture ne change pas. Cette version réduit
45 alertes à huit en retirant les formes courtes qui sont aussi des mots ordinaires
et la détection générale des acronymes entre parenthèses. Les huit relectures
ajoutent STT, NWSA, WBD, SBUX, JPM, BLK, NWSA et IVZ, tous neutral, sans perte.
Cela mesure la couverture des alertes configurées, pas le rappel absolu.

Après cette revue, `entity-sentiment-v5-rcorcf` précise qu'une performance
historique ou un faible mouvement de pair utilisé seulement comme comparaison
reste neutre. Il exige aussi d'évaluer séparément les effets d'un accord pour
chaque partie. Deux exemples synthétiques couvrent ces décisions. Le registre
`entity-aliases-v3` ajoute CNN → WBD ; cette relation avait été retrouvée par la
relecture de N013 mais n'était pas encore codifiée.

La passe complète v5 confirme les trois corrections recherchées : NVDA/N069 et
les petits mouvements de pairs de N091 deviennent neutral ; AAPL/N095 devient
neutral tandis que QCOM reste positive. Elle produit toutefois 220 paires contre
225 après la relecture v4, omet plusieurs sources, marques ou filiales neutres et
ajoute deux faux `XYZ` à partir du réseau social X. Elle modifie aussi 23 labels,
dont des régressions manifestes comme BAC/N092, négatif pour avoir dégradé Nike.
Une meilleure règle de prompt n'élimine donc ni la variance ni le besoin de
contrôles déterministes et d'une composition explicite.

## v6 : rôle explicite et neutralité imposée par le schéma

Les 19 différences entre la composition manuelle et `run-final-v1` portent presque
toutes sur la frontière entre « implication » et « simple mention » : banque qui
émet une note, concurrent cité, partie à un accord, source. Le PDF définit ces
mentions comme neutres. `entity-sentiment-v6-roles` demande donc d'abord un rôle par
entreprise : `subject`, `counterparty` ou `affected_peer`, qui peuvent porter un label
directionnel, ou `rating_issuer`, `source`, `comparison` ou `other_mention`, qui
sont toujours neutres.

La règle est appliquée trois fois :

1. Le prompt définit chaque rôle et départage `affected_peer` et `comparison` : une
   conséquence propre à l'entreprise doit être écrite dans l'article.
2. Le schéma JSON strict contient deux branches `anyOf` : un rôle toujours neutre
   ne peut pas être généré avec un autre label que `neutral`.
3. Le validateur Python refuse un rôle inconnu ou incohérent, y compris depuis le
   cache.

Le rôle reste interne (`classifications.json`) ; les CSV livrés ne changent pas. Il
donne aussi la distinction « sujet / simple mention » demandée par le sujet. Un
treizième exemple fictif couvre un concurrent affecté, une comparaison et une source.
Le registre `entity-aliases-v6` ajoute Xbox → MSFT, Citi → C, KeyBanc → KEY,
Truist → TFC et Visible Alpha → SPGI, observés dans les données.

## Contrôles après le modèle

Le registre actif `entity-aliases-v5` complète le prompt sans lui déléguer la
décision finale. Il ajoute quatre relations stables observées dans les données
(CNBC/NBC News, CBS/CBS News, Barron's et Kenworth) et deux associations
interdites (`X → XYZ`, `SpaceX → XOM`). La commande `compose` utilise ces règles
pour signaler les omissions ou faux rattachements ; elle ne réécrit ni un ticker
ni un label. Sa recette est versionnée séparément sous
`classification-composition-v1`.

## Structure RCORCF

La source du prompt est `SYSTEM_PROMPT` dans `src/aie2609/classification.py`.
Les titres suivent l'ordre demandé, avec leur équivalent anglais ; les consignes
restent en anglais comme les articles et les labels. Le prompt est transmis par
le champ `instructions` de Responses, et les données dans deux messages séparés.

| Partie | Contenu concret |
| --- | --- |
| Rôle | Annotateur de sentiment financier par entreprise ; exhaustive identification des mentions, prudence sur les inférences |
| Contexte | Article entier, date de publication, univers fermé, texte déjà normalisé ; agrégation temporelle effectuée ensuite par le code |
| Objectif | Identifier les entreprises, résoudre noms/classes/filiales, puis attribuer un sentiment propre à chacune |
| Résultat | Une entrée par entreprise éligible, y compris neutre, avec un extrait exact permettant la revue |
| Contraintes | Données non fiables, pas d'outils, pas de ticker inventé, pas de raisonnement publié, pas de score calculé par le modèle |
| Format | Objet JSON strict `entities`, champs `ticker`, `label`, `evidence`, ordre stable, liste vide définie et exemples complets |

Les règles précisent la différence entre absence, neutralité et identité
incertaine ; les noms ressemblants en Unicode ; les sources et banques analystes ;
les filiales dont le parent n'est pas écrit ; les participations minoritaires ;
les nouvelles contradictoires, anciennes ou niées ; les comparaisons incidentes.
Une instruction citée dans un article reste une donnée à analyser.

## Douze exemples fictifs intégrés

1. Dégradation de FIS par Wells Fargo : FIS négatif, banque neutre.
2. Contrat gagné par Nvidia et perdu par AMD : implications opposées explicites.
3. Rappel Tesla et comparaison avec Waymo : Tesla négatif, Alphabet neutre via
   sa filiale. Le lien parent est une hypothèse d'identité établie de cet exemple.
4. Alphabet, YouTube et classes GOOG/GOOGL : une seule entrée canonique.
5. Startup hors univers et pilote Microsoft : Microsoft neutre, aucun concurrent
   ajouté à partir du seul secteur d'activité.
6. Apple : résultat ancien favorable, prévision actuelle défavorable.
7. Microsoft : effets explicitement compensés, perspective inchangée et neutralité.
8. Mots « A », « IT » et indice Nasdaq : pas d'entreprises identifiées à tort.
9. Startup privée sans parent éligible identifiable : liste vide, pas de parent
   inventé à partir d'une éventuelle participation minoritaire connue.
10. Rappel Apple et instruction malveillante dans le texte : instruction ignorée.
11. Contrat AMD et performance historique de Nvidia citée en comparaison : AMD
    positif et Nvidia neutre.
12. Licence Qualcomm–Apple dont le bénéfice documenté concerne Qualcomm : QCOM
    positif et Apple neutre.

Chaque exemple définit son petit univers, son article, sa réponse JSON complète
et une note pédagogique. Les événements et chiffres sont fictifs, sans collecte
métier externe. Ils ne doivent pas être recopiés dans les résultats réels.

Le cas Waymo étant désormais enseigné dans le prompt, N027 sert à vérifier une
régression connue, pas à mesurer indépendamment la généralisation. Prévoir aussi
des articles distincts, avec annotations relues par un humain avant de consulter
les prédictions, pour évaluer rappel des entreprises et justesse des sentiments.

## Que signifient les deux versions ?

`PROMPT_VERSION = "entity-sentiment-v5-rcorcf"` identifie **nos consignes d'analyse**.
La faire évoluer quand les instructions, exemples ou règles de classification
changent. Ce n'est pas la version du modèle OpenAI, qui reste `gpt-5.6-terra`.
v3 ayant déjà été utilisée dans un essai, cette refonte porte un nouvel identifiant
v4 plutôt que de donner deux sens différents à v3. La précision issue de la
revue complète porte v5. Revenir à un ancien prompt
exact peut reprendre son ancien identifiant ; ne pas réutiliser ce nom pour une
nouvelle variante. Le tag est géré explicitement par le développeur.

`NORMALIZATION_VERSION = "nfc-lf-u200b-v1"` identifie **la préparation du texte**
dans `normalization.py`, avant l'analyse :

- `nfc` : harmonisation Unicode NFC des caractères équivalents ;
- `lf` : harmonisation des fins de ligne CRLF/CR vers LF ;
- `u200b` : retrait du caractère espace de largeur nulle U+200B, avec comptage ;
- `v1` : première version de cette politique.

Exemple explicatif : `Te<U+200B>sla` devient `Tesla` dans la copie normalisée.
Les identifiants structurants sont aussi débarrassés des espaces de bord. Les
fichiers fournis restent intacts. Cette version ne concerne ni le modèle ni une
normalisation mathématique des scores. La réécriture du prompt ne change pas ce
nettoyage : elle reste donc à v1. Une future modification du nettoyage devra
modifier le code concerné et son tag, pas seulement le tag.

## Pourquoi ces versions entrent dans le cache ?

La clé de cache SHA-256 prend en compte la requête complète (dont texte normalisé,
univers, consignes, schéma, modèle et paramètres) et les deux tags. Un changement
de consignes ou de politique de nettoyage doit empêcher de réutiliser par erreur
une analyse faite dans d'autres conditions. Même si le développeur oubliait de
modifier le tag du prompt, changer ses consignes change déjà l'empreinte de la
requête ; le tag apporte une trace lisible dans les rapports.

Les anciens fichiers de cache restent conservés, mais ne correspondent plus aux
nouvelles requêtes. Une nouvelle analyse peut donc entraîner de nouveaux appels
facturés. Les tests vérifient séparément que chaque tag change l'empreinte. La
version de normalisation est actuellement incluse dans cette empreinte ; seul
le tag de prompt est aussi exposé explicitement dans le manifeste.

## Validation et limites

Les tests lisent directement les exemples du prompt et contrôlent JSON strict,
univers, labels, unicité, tri et extraits exacts. Ils ne vérifient pas la capacité
du modèle à reproduire les décisions. Une prévisualisation confirme que les
requêtes sont constructibles et leurs nouvelles clés diffèrent du pilote v2.
Plus de détail augmente la taille des requêtes sans garantir une meilleure
qualité. Le retest sur les trois articles connus est favorable, mais constitue
une vérification de régression, notamment parce que le cas Waymo est enseigné.
Comparer aussi sur un échantillon distinct avant adoption pour le jeu complet ;
modèle et effort de raisonnement sont restés fixes lors du retest.

Références de conception : le [guide OpenAI sur les prompts](https://developers.openai.com/api/docs/guides/prompt-engineering)
préconise des consignes structurées et des exemples de sorties. Le [guide des
modèles de raisonnement](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
recommande des consignes claires et des délimitations, sans demander de transcript
du raisonnement. RCORCF est ici la structure demandée par l'utilisateur ; ce n'est
pas présenté comme une méthode officielle OpenAI ou une garantie de précision.
