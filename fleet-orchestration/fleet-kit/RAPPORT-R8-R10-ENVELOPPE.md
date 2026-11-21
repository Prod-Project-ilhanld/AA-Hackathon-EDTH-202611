# R8 / R10 / enveloppe anti-zéro — Martin

Chantier : séparation (R8), synchronisation (R10), enveloppe anti-zéro, `check_handin.py` à chaque version.
Branche : `feature/enveloppe` (contient `main` à `55327de`, la v7 de Louis, et `feature/tests-r8-r10-enveloppe`).
Code des autres non modifié : `planner.py` et `routing.py` sont identiques à `main`. Tout passe par
`handin/deconflict.py` (fichier de départ prévu pour ce chantier) et des fichiers de test nouveaux.

## Résumé

| Point | Statut |
|---|---|
| Audit R8 (séparation 40 m) | Fait : tous les cas rejetés, limite exacte 40 m acceptée |
| Audit R10 (tout-ou-rien, 20 s) | Fait : désynchronisation, effecteur manquant/en trop, > 25 m rejetés |
| Faille 1 : R10 entre deux essais | **Corrigée** (garde R10 dans `deconflict.adjust`, active par défaut) |
| Faille 2 : pas de repli sur `greedy_plan` | **Prouvée, non corrigée** : patch proposé dans `proposals/`, à appliquer par Louis |
| Ordonnanceur de décollage R8 (CP2 / Going further) | Fait, **désactivé par défaut** : +2,11 % total, +3,42 % L4 |
| `check_handin.py` sur `main` + les deux branches | **8/8 ok**, 4229,6 vs 2748,6, 38,3 s max, aucune régression |

## Faille 1 — R10 entre deux essais : corrigée

Le `_try` incrémental valide les routes touchées seules ; sa docstring dit que R8 est la seule règle qui couple les
routes, mais R10 les couple aussi (un hostile exige exactement ses effecteurs, à 20 s près).

- Forcée (`tests/test_latent_guards.py`) : servir deux fois le même contact (ce que ferait une boucle de réparation)
  est accepté et le plan devient invalide (R10) dans **6 cas sur 6** (scénario manuel, L2-0, L3-0 × RoutedPlanner,
  FastPlanner). Aujourd'hui `build` sert chaque contact une seule fois, donc elle ne se déclenche pas seule.
- Correction : `deconflict.adjust`, déjà appelé en premier dans `_try`, rejette un candidat dont les engagements,
  réunis avec les engagements acceptés du même hostile, cassent R10 (nombre par sous-type ou fenêtre de 20 s).
  Un tel candidat est invalide pour le validateur officiel : aucun plan valide n'est perdu.
  Active par défaut, `PLANNER_R10_GUARD=0` la coupe.
- Vérifié : avec la garde, la seconde passe est rejetée et le plan reste valide ; une construction normale est
  identique avec ou sans garde ; le test d'audit R10 de `test_planner_r8_r10.py` passe désormais ;
  `test_planner_robustness.py` de l'équipe : 12 OK.

## Faille 2 — pas de repli sur greedy_plan : prouvée, non corrigée

L'enveloppe de `main` est solide (plan vide écrit avant la recherche, alarme à 52 s, écritures atomiques,
validateur officiel en garde finale, sortie toujours à 0), mais le dernier recours reste le plan vide.

- Forcée (`tests/test_latent_guards.py`) : si toutes les constructions plantent (régression dans le builder),
  `solve()` écrit un plan valide à **0,0**, alors que le glouton du kit donne **281,3** sur L2-0.
- La correction est dans `solve()` de `planner.py` (code de Louis) : non appliquée.
  Patch proposé : `proposals/greedy_fallback.patch` (repli sur `fk.baseline.greedy_plan` si rien de valide et positif,
  seulement s'il reste au moins 8 s avant l'alarme ; `greedy_plan` + `evaluate` mesuré à 2,7 s max sur L4, graines 0-2).
  Vérifié sur une copie jetable : 281,3 au lieu de 0,0. Il s'applique proprement : `git apply fleet-orchestration/fleet-kit/proposals/greedy_fallback.patch`.
  Le test correspondant est marqué `expectedFailure` et passera en « unexpected success » une fois le patch appliqué.

## Ordonnanceur de décollage R8 (`deconflict.py`)

Pour chaque candidat de `_try` en conflit R8, il retarde le décollage de toute la route jusqu'au premier créneau
à 40 m de toutes les routes acceptées (saut par intervalle de conflit, pas doublé, puis dichotomie).
Un groupe d'effecteurs reçoit un retard commun, puis chaque membre encore en conflit avec un voisin est retardé seul,
sans dépasser la fenêtre de synchronisation de 20 s (R10), la fenêtre de frappe (R9) ni l'horizon ; le scout reste fixe.
Les candidats sans espoir (R7, confirmation R4 perdue) ne sont pas décalés ; le candidat décalé est re-vérifié.

Bench apparié, `tools/bench.py`, 38 s, `main` actuel, graines 10-13 jamais utilisées pendant le développement :

| Niveau | Éteint | Allumé | Écart |
|---|---|---|---|
| L1 | 354,1 | 353,3 | -0,23 % |
| L2 | 965,0 | 968,1 | +0,32 % |
| L3 | 2032,0 | 2044,9 | +0,63 % |
| L4 | 4248,0 | 4393,1 | **+3,42 %** |
| Total | 7599,1 | 7759,4 | **+2,11 %** |

16/16 plans valides dans les deux séries, 38,9 s max ; 12 scénarios en hausse, 1 en baisse, 3 égaux ; les 4 L4 en
hausse (+70,9, +11,3, +35,4, +27,5). Le bruit entre deux exécutions identiques est de 0,1 à 0,5 % (CP1 du tableau) :
le gain L4 est au-dessus, L1/L2 est dans le bruit. Même tendance sur l'ancien planner (graines 0-3 : +2,3 %, L4 +3,2 %).

Pourquoi il est encore éteint : la règle de l'équipe demande un gain apparié sur au moins 20 graines L4
(≤ 40 % de graines en baisse, 0 invalide) ; il n'y en a que 8 (8/8 en hausse, 0 invalide). Et le jury ne transmet
aucune variable d'environnement (`check_handin.py` non plus) : pour que le gain compte, il faut `ENABLED = True`
par défaut dans `deconflict.py`. Décision d'équipe, après le bench sur 20 graines L4.

## check_handin.py

Sur `feature/enveloppe` (`main` + les deux branches + la garde R10), environnement du jury :
8/8 ok, 0 échec, total **4229,6** contre 2748,6 pour la baseline, temps max **38,3 s**, code de sortie 0.
Identique, scénario par scénario, à la v7 seule (même total 4229,6).

| Scénario | Score | Baseline | Temps |
|---|---|---|---|
| L1-0 | 125,8 | 123,8 | 12,5 s |
| L1-1 | 72,0 | 68,8 | 12,4 s |
| L2-0 | 293,8 | 281,3 | 38,1 s |
| L2-1 | 349,3 | 338,9 | 38,1 s |
| L3-0 | 608,0 | 449,1 | 38,1 s |
| L3-1 | 514,0 | 463,9 | 38,1 s |
| L4-0 | 1137,8 | 590,3 | 38,2 s |
| L4-1 | 1129,0 | 432,5 | 38,3 s |

## Tests (depuis `fleet-kit/`, unittest, sans pytest)

| Fichier | Résultat |
|---|---|
| `tests/test_deconflict.py` | 10 OK |
| `tests/test_latent_guards.py` | 4 OK + 1 échec attendu (repli glouton, patch non appliqué) |
| `tests/test_planner_r8_r10.py` | 12 OK |
| `tests/test_planner_envelope.py` | 1 OK + 1 échec attendu (`greedy_plan` jamais appelé) |
| `tests/test_planner_robustness.py` (équipe) | 12 OK |

## Avec plus de temps

- bench apparié sur 20 graines L4 (critère de l'équipe) puis, s'il passe, `ENABLED = True` par défaut ;
- phase 2 du scheduler (CP3) : retard au sol → couche d'altitude → détour ; strike groups sur couches séparées ;
- réduire le coût du scheduler (il divise le nombre d'essais par seconde sur L4) ;
- mode déterministe (CP1) pour distinguer les gains < 1 % du bruit.
