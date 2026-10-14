# Référence reference-v1 — qui a arbitré et comment

Généré par `prepare-reference` le 14 octobre 2026 à partir de six versions complètes :
la composition manuelle (`output/composition-final-v3`), `run-final-v1`, les trois
passes v6 et leur vote (`output/run-v6-vote3`). 239 couples article/ticker :
203 unanimes et 36 disputés, plus 25 contrôles tirés au hasard parmi les unanimes
(graine 20260929), soit 61 cas.

## Arbitre

Les décisions de `cases.csv` ont été prises par **l'agent de développement
(Claude)**, à la demande de l'utilisateur, et non par un humain. La colonne
s'appelle `human_decision` pour rester compatible avec l'outil. Chaque note commence
par `agent;`. Garde-fous et limites :

- Les définitions appliquées sont celles du sujet (page 4), rappelées dans `GUIDE.md`.
- `GUIDE.md` et `cases.csv` ne montrent pas quelle version a proposé quoi, et
  `key.json` n'a été ouvert qu'après le calcul du score. L'arbitrage n'est toutefois
  pas totalement aveugle : l'agent avait déjà vu, en conversation, les labels de
  certaines versions pour N039, N047, N091 et N095.
- C'est un autre modèle que `gpt-5.6-terra`, donc une autre famille d'erreurs, mais
  ce n'est pas une vérité terrain humaine.
- 21 décisions sont notées `debatable` : un annotateur raisonnable pourrait trancher
  autrement. L'utilisateur a relu les justifications de R004 (PCG), R008-R009 (AMZN,
  HD) et R013 (ADBE), les a jugées discutables mais défendables, et a validé
  l'ensemble sans modifier de décision.

## Résultat (`score-reference --dir review/reference-v1`)

| Version | Cas disputés justes (36) | Disputés non discutables (20) | Exactitude estimée |
| --- | --- | --- | --- |
| manuel | 15 | 9 | 0,878 |
| run-final-v1 | 22 | 17 | 0,907 |
| v6-passe1 | 25 | 17 | 0,920 |
| v6-passe2 | 25 | 16 | 0,920 |
| v6-passe3 | 26 | 16 | 0,924 |
| **v6-vote3** | **28** | **19** | **0,933** |

Contrôles du consensus : 24 sur 25 conformes (0,96). Le seul écart, D/N045, est une
décision discutable de l'arbitre. L'exactitude estimée applique ce taux aux
203 couples unanimes. Elle ne mesure ni les entreprises omises par toutes les
versions, ni l'écart avec la référence des évaluateurs.

Les 9 erreurs restantes de v6-vote3 : PCG/N020, GM/N038, GS et MS/N047, AMZN/N048,
RCL/N049, RCL/N055 et D/N045, toutes notées discutables, ainsi que JBL/N088 (contrat
gagné classé neutre).
