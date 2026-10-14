# AIE2609 — sentiment financier par entreprise

## Quick start (English)

Python 3.12+. Put `news.json` and `sp500.csv` in the repository root and set
`OPENAI_API_KEY` (environment variable or a local `.env` file).

```bash
python -m venv .venv
# Linux/macOS: .venv/bin/python   Windows: .venv\Scripts\python.exe
.venv/bin/python -m pip install --require-hashes -r build-requirements.lock -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m unittest discover -s tests                       # offline tests
.venv/bin/python -m aie2609 run --max-cost-usd 10                    # end to end
```

The run writes `output/run-<UTC timestamp>/final/entities.csv` and `scores.csv`
and prints calls, tokens, total cost and cost per article. Submitted outputs are in
[`results/`](results/README.md). Documentation below is in French.

## Présentation

Pipeline Python en ligne de commande :

```text
news.json + sp500.csv
        ↓
identification et sentiment par entreprise
        ↓
contrôles et revue ciblée
        ↓
score temporel par ticker
        ↓
entities.csv + scores.csv
```

Le modèle classe chaque entreprise mentionnée dans un article en `positive`,
`neutral` ou `negative`. Le code vérifie les réponses, rattache les classes et
filiales connues, puis calcule :

```text
weight = 0.5 ** (age_in_days / 7)
score(ticker) = somme(label_value × weight)
```

La date de référence imposée est `2026-09-29T00:00` en `America/New_York`.

## Commande de bout en bout

```powershell
.\.venv\Scripts\python.exe -m aie2609 run --max-cost-usd 10
```

Par défaut : trois passes avec vote majoritaire et jusqu'à trois tentatives par
article, la configuration mesurée comme la plus fiable (voir « État actuel »).
Coût attendu à cache froid : environ 4,5 USD, soit 0,045 USD par article ;
`--passes 1` divise le coût par environ 1,5 car les passes 2 et 3 relisent le
cache fournisseur.

Chaque passe enchaîne les étapes ci-dessous dans `pass-N/`, puis le vote est composé
et exporté dans `output/run-<horodatage UTC>/` (ou `--output-dir`, qui doit être
nouveau). Avec `--passes 1`, les étapes sont directement dans le dossier du run :

1. `classify/` : les 100 articles avec le prompt actif ;
2. `review/<ID>/` : uniquement les articles portant une alerte bloquante. Une
   omission fiable passe en mode `additions-only` ; un alias interdit (par exemple
   `X → XYZ`) passe en relecture ciblée qui peut retirer l'entité. Une relecture
   invalide ou incomplète est rejetée et la première passe validée est conservée ;
3. `compose/` : composition avec provenance et alertes ;
4. `final/entities.csv`, `final/scores.csv` et leur manifeste ;
5. `run_report.json` : relectures, alertes, appels, tokens connus et coût par article.

`--passes 3` lance trois passes indépendantes (classification, relectures et
composition), chacune avec sa propre réplique du cache, puis garde chaque couple
proposé par au moins deux passes avec son label majoritaire. Si les passes sont
partagées sur le label, le couple devient `neutral` et il est signalé.
`vote/vote_report.json` donne pour chaque couple les votes et son niveau d'accord
(`unanimous`, `majority`, `label_tie`, `dropped_minority`). Le coût est multiplié
par le nombre de passes.

Lorsqu'une réponse est refusée par le validateur, la tentative suivante transmet au
modèle le motif fixe du refus (jamais le texte rejeté) ; les tentatives restent
bornées par `--max-attempts`.

En fin de run, la console affiche les appels, reprises, tokens par catégorie,
coût total, coût par article et coût par étape. Le même résumé se relit sans API :

```powershell
.\.venv\Scripts\python.exe -m aie2609 usage --run-dir output/run-final-v1
```

`--json` donne la version machine. Le détail par tentative (tokens, coût, durée,
identifiant de réponse) reste dans chaque `usage.json`.

Le run écrit toujours les CSV lorsque toutes les étapes réussissent. S'il reste
des alertes bloquantes, le statut vaut `completed_with_alerts` et le manifeste
porte `ready_for_scoring: false`. La commande `export` seule reste stricte.
Une erreur réseau, de budget ou de coût inconnu arrête le run (`status: failed`).
`--dry-run` prévisualise les requêtes sans clé ni appel.

## État actuel

**Version retenue : `output/run-v6-vote3/final/`**, produite par `run --passes 3`
avec le prompt `entity-sentiment-v6-roles`.

- 100 articles, 500 entreprises canoniques après regroupement des doubles classes.
- 233 couples article/ticker : 61 `positive`, 117 `neutral`, 55 `negative` ;
  112 tickers dans `scores.csv`. Statut `completed`, zéro alerte bloquante.
- Stabilité : les trois passes indépendantes donnent le même résultat sur 224 des
  239 couples proposés (93,7 %) ; le vote garde 9 couples à deux voix contre une et
  en écarte 6 proposés par une seule passe.
- Fiabilité mesurée sur la référence [`review/reference-v1`](review/reference-v1/README.md),
  arbitrée par l'agent avec des définitions du sujet ; ce n'est pas une référence
  humaine. Exactitude estimée par couple : **0,933** pour la version retenue,
  0,907 pour `run-final-v1` (une passe, prompt v5) et 0,878 pour l'ancienne
  composition manuelle. Sur les 20 cas disputés non discutables : 19, 17 et 9 justes.
- Coût du run retenu : 2,97 USD avec 65 réponses rejouées depuis un run interrompu ;
  coût à froid estimé à 0,045 USD par article pour trois passes, et mesuré à
  0,030 USD par article pour une passe (`run-final-v1`).
- 100 tests hors réseau passent.
- Budget : 14,70 USD engagés au total sur les 100 USD autorisés.

Les versions précédentes restent comme preuves : `output/run-final-v1/` (une passe,
prompt v5) et `output/final-results-v1/` (composition manuelle v4, non reproductible
par la commande actuelle).

## Fichiers importants

| Fichier | Rôle |
| --- | --- |
| `news.json` | 100 articles fournis, jamais modifiés |
| `sp500.csv` | Univers d'entreprises autorisé, jamais modifié |
| `output/run-v6-vote3/final/entities.csv` | Livrable : une ligne par article et ticker |
| `output/run-v6-vote3/final/scores.csv` | Livrable : score temporel par ticker |
| `output/run-v6-vote3/run_report.json` | Passes, relectures, vote, alertes, coût |
| `output/run-v6-vote3/vote/vote_report.json` | Votes et niveau d'accord par couple |
| `review/reference-v1/` | Référence arbitrée, score par version et limites |

Les dossiers `output/`, `.cache/` et `.env` sont ignorés par Git. Les deux CSV
finaux devront donc être joints explicitement lors de la remise.

## Installation

Environnement testé : Python 3.12.10 sous Windows PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r build-requirements.lock -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
```

## Vérifications rapides

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -m aie2609 audit --news news.json --universe sp500.csv
```

Ces commandes n'utilisent ni clé API ni réseau.

## Mesurer la fiabilité : référence arbitrée à l'aveugle

```powershell
.\.venv\Scripts\python.exe -m aie2609 prepare-reference `
  --version A=chemin\classifications.json --version B=autre\classifications.json `
  --spot-checks 25 --output-dir review/reference-new
.\.venv\Scripts\python.exe -m aie2609 score-reference --dir review/reference-new
```

Chaque couple article/ticker où les versions divergent devient un cas à arbitrer,
plus un échantillon aléatoire de couples unanimes. `cases.csv` et `GUIDE.md` ne
montrent pas quelle version a proposé quoi ; `key.json` garde cette information
pour le score. Le score donne, par version, les cas disputés justes, les erreurs,
l'exactitude mesurée du consensus et une exactitude estimée sur tous les couples.

## Évaluer les désaccords

1. Ouvrir le guide lisible :
   [`review/human-evaluation-v1/SAMPLE_GUIDE.md`](review/human-evaluation-v1/SAMPLE_GUIDE.md).
2. Dans [`sample.csv`](review/human-evaluation-v1/sample.csv), remplir uniquement
   `human_decision` et éventuellement `human_notes`.
3. Utiliser une de ces valeurs : `positive`, `neutral`, `negative`, `absent` ou
   `uncertain`.
4. Calculer l'accord avec chaque version :

```powershell
.\.venv\Scripts\python.exe -m aie2609 evaluate --sample review/human-evaluation-v1/sample.csv
```

`absent` signifie que l'entreprise ne devrait pas figurer pour cet article.
`uncertain` conserve le cas dans le rapport sans le compter dans la précision.
Les annotations humaines ne modifient jamais automatiquement les classifications.
Le résultat mesure la qualité relative sur les cas disputés ; il ne constitue pas
un taux de précision global sur les 230 classifications.

Pour régénérer le même matériel de revue :

```powershell
.\.venv\Scripts\python.exe -m aie2609 prepare-evaluation `
  --final output/composition-final-v3/classifications.json `
  --candidate output/full-100-v5-final/classifications.json `
  --cases N069:NVDA N091:GOOGL N095:AAPL N092:BAC N076:NVDA N047:GS N039:ADBE N028:AMZN N071:JPM N081:WBD `
  --output-dir review/human-evaluation-new
```

Le dossier de sortie doit être nouveau afin de préserver les annotations existantes.

## Exécuter une classification

Le modèle imposé est `gpt-5.6-terra`. La clé doit rester dans `OPENAI_API_KEY` ou
dans un fichier local `.env` ignoré par Git :

```dotenv
OPENAI_API_KEY=COLLER_LA_CLE_ICI
```

Prévisualisation sans appel :

```powershell
.\.venv\Scripts\python.exe -m aie2609 classify --ids N001 N002 N027 --dry-run
```

Exécution bornée :

```powershell
.\.venv\Scripts\python.exe -m aie2609 classify `
  --ids N001 N002 N027 `
  --max-cost-usd 1 `
  --max-attempts 1 `
  --output-dir output/pilot-new
```

Chaque dossier de run doit être nouveau. Aucun autre modèle n'est utilisé si
`gpt-5.6-terra` échoue.

## Composition et export

`compose` vérifie les revues, leur provenance, les omissions connues et les
associations interdites. `export` accepte uniquement une composition marquée
`ready_for_scoring=true` dont l'empreinte correspond au JSON.

```powershell
.\.venv\Scripts\python.exe -m aie2609 export `
  --composition-dir output/composition-final-v3 `
  --output-dir output/final-results-new
```

L'export écrit exactement :

- `entities.csv` : `id,ticker,label` ;
- `scores.csv` : `ticker,value` ;
- `run_manifest.json` : paramètres et empreintes SHA-256.

## Limites actuelles

- Les validations structurelles ne prouvent pas la justesse des sentiments.
- La relecture utilise le même modèle que la première passe.
- Le registre de marques et filiales est volontairement limité aux relations
  établies dans le projet.
- Les résultats décrivent seulement les articles fournis ; ce ne sont pas des
  recommandations d'investissement.
- Les décisions humaines du petit échantillon doivent être terminées avant de
  choisir définitivement entre les labels en désaccord et de régénérer les CSV.

## Documentation détaillée

- [AGENTS.md](AGENTS.md) — règles de travail et de sécurité.
- [ARCHITECTURE.md](ARCHITECTURE.md) — responsabilités des modules.
- [DATA_MODEL.md](DATA_MODEL.md) — contrats et formule exacte.
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — lots et état d'avancement.
- [docs/FULL_100_REVIEW.md](docs/FULL_100_REVIEW.md) — analyse des 100 articles.
- [docs/PROMPT_DESIGN.md](docs/PROMPT_DESIGN.md) — prompt RCORCF et versions.
- [docs/WORK_LOG.md](docs/WORK_LOG.md) — commandes, coûts et décisions historiques.
