# Fleet Orchestration : livrable d'équipe (EDTH x Adopt AI, Alta Ares SUB-15)

Mis à jour le 2026-11-21 (planner v7). Les chiffres marqués MESURÉ viennent de `fleet-kit/tools/bench.py` ; ceux marqués À MESURER ne sont pas encore connus. Aucun chiffre n'est inventé.

## Problème
Une flotte mixte (scouts qui observent et rentrent, effecteurs à sens unique) doit servir des contacts sous dix règles (séparation 40 m, zones interdites, confirmation avant engagement, fenêtres de temps, tout ou rien, énergie). Un plan invalide vaut 0. Le jury note la somme des scores sur des scénarios cachés, puis la solidité et la présentation.

## Solution (planificateur de Louis, `fleet-kit/handin/planner.py`)
Glouton du kit élargi et rendu rapide :
- les 15 scouts les plus proches de chaque hostile avec toutes les options (donc tous les scouts de L4 ; le baseline en essaie 3), au-delà de 15 les autres avec les options simples : sur L4 les scouts proches sont saturés pendant que d'autres restent au sol ;
- contrôle incrémental à chaque essai (routes touchées seules, séparation R8 contre les autres, score par différences) à la place de la validation complète du plan entier, qui prenait 70 % du temps d'une construction : 3 fois plus d'essais par seconde ; le scorer du kit valide quand même chaque plan gardé et le plan final (v5) ;
- relances de l'ordre des contacts (points par effecteur requis, puis petites variations autour du meilleur ordre) pendant 38 s, sur plusieurs processus, avec deux routages : celui du kit et le module de routage 3D de l'équipe (`handin/routing.py`, 7thwardlord1) ; on garde le meilleur plan valide ;
- chaque pas accepté a passé `evaluate`, le plan final est revalidé, repli sur le meilleur plan valide ;
- filet de sécurité de l'équipe (PR 1) : plan vide valide écrit avant toute recherche, écritures atomiques, alarme à 52 s, copie des fonctions du kit dans `handin/fk/` (le planner ne dépend pas d'un `fleetkit` importable), contrôle final avec le validateur officiel, code de sortie toujours 0.

MESURÉ, planner v1, 50 graines par niveau (200 cas, sous-processus, limite 60 s) : 200/200 valides, temps max 38,2 s. Contre le baseline du kit sur les mêmes graines : L1 5008,7 contre 4754,7 (+5,3 %) ; L2 12367,3 contre 11383,6 (+8,6 %) ; L3 23214,6 contre 19397,1 (+19,7 %) ; L4 38664,6 contre 26160,4 (+47,8 %).
MESURÉ, planner v2 (relances parallèles, ordre par points par effecteur), graines 0 à 7 : 16/16 valides ; L3 3977,1 contre 3887,1 pour la v1 (+2,3 %) ; L4 6341,0 contre 5708,5 (+11,1 %). Avec un seul cœur : L3 3939,7 ; L4 6185,0. MESURÉ, planner v2, 50 graines par niveau (200 cas, 2 processus par cas, donc estimation basse) : 200/200 valides, temps max 38,2 s ; L1 5008,7 ; L2 12343,3 ; L3 23613,6 (+1,7 % contre la v1) ; L4 40940,2 (+5,9 % contre la v1, ×1,565 le baseline) ; total 81905,8 contre 79255,2 pour la v1.

## Ce qui nous distingue
- Un zéro est le pire résultat : garde-fous (validation finale, repli) avant tout gain de score.
- Un banc reproductible (`tools/bench.py`) qui lance le planner comme l'évaluation (sous-processus, 60 s) et compare au baseline.
- Diagnostic chiffré des pertes : sur L4 graine 3, 10 hostiles sont bloqués par R7 et beaucoup d'autres sont physiquement hors de portée (aller-retour au-delà de l'horizon de 900 s). Le plafond de score est donc plus bas qu'il n'y paraît.
- Plans expliqués : rapport d'explication de Swann (critères réels : score net, ordre par points, scouts/altitudes/angles/délais testés).
- Perte de liaison traitée dans un mini-simulateur à nous (`fleet-kit/linkloss/`, isolé du plan remis) : plans à marges, politiques continue / retour / ajustement, courbe de dimensionnement (voir la section Perte de liaison).

## Travail de l'équipe (passé et à venir)
| Qui | Fait | À venir |
|---|---|---|
| Louis | kit lu, baseline mesuré, banc 50 graines, planner v1 à v7 (avec le routage de l'équipe), tests de robustesse, mini-simulateur link-loss et courbe de dimensionnement, étude de passage à l'échelle | terminé côté code ; démo |
| 7thwardlord1 | routage 3D `handin/routing.py` et ses tests, utilisé par le planner | à confirmer |
| Mahmoud (compte `mkassaby`, à confirmer) | PR 1 d'intégration : filet de sécurité, `handin/fk/`, CI, `docs/PLAN.md` et `docs/ROADMAP.md`, fichiers de départ `targets.py` et `deconflict.py` (désactivés) | pilotage de `main`, points d'équipe |
| Martin | audite R8 et R10 d'après le rapport de Swann | à confirmer |
| Swann | démo `swann_demo.py` (calques du viewer, rapport d'explication), rapport L4 graine 3 (glouton 532,9) | rapport d'explication sur les plans du moteur (branche `feature/planner-v1`) |
| Ilhan | accès au repo d'équipe, piste « scouts au sol » | à clarifier |
| Les autres membres | non communiqué | à renseigner |

## Lancement en une commande
```sh
cd fleet-orchestration/fleet-kit && python3 handin/check_handin.py
```
Un scénario à la main : `python3 -m fleetkit generate L4 3 -o scenario.json && python3 handin/planner.py scenario.json plan.json && python3 -m fleetkit view scenario.json plan.json --open`

## Script de démo, 2 minutes (à jouer avec les chiffres du banc)
1. Accroche (15 s) : un plan invalide vaut 0, donc la sécurité passe avant le score.
2. Moment fort (60 s) : même scénario L4 graine 3, baseline 532,9 contre notre plan v7 1076,7, soit +102 % (MESURÉ, un seul scénario), dans le viewer ; montrer pourquoi tel hostile est servi et tel autre refusé (R7, horizon, énergie), avec le rapport de Swann.
3. Preuve (30 s) : sortie de `bench.py` sur 50 graines par niveau : 0 invalide, temps maximal 39,6 s (v7, MESURÉ).
4. Fermeture (15 s) : limites et suite.

## Limites connues
- Heuristique gloutonne avec relances, pas d'optimum prouvé ; aucune borne supérieure calculée.
- Utilise 38 s sur L2 à L4 ; sur L1 (5 avions) la recherche s'arrête quand rien de mieux n'a été trouvé depuis 12 s (12 s en moyenne, mêmes scores que 38 s sur 50 graines). Un arrêt anticipé sur L2 a coûté 0,3 % et n'a pas été gardé.
- Les versions 2 à 4 profitent de plusieurs cœurs ; à 1 cœur la v4 reste au-dessus de la v3 sur L4 (graines 0 à 7 : 6940,9 contre 6273,6 pour la v3 à 2 cœurs).
- Sur L4 graine 3, 10 hostiles sont interdits par R7 et plusieurs autres sont hors d'atteinte (aller-retour au-delà de 900 s) : le plafond réel est plus bas que le total des points.
- Perte de liaison : modélisée dans NOTRE simulateur (une seule perturbation, le ralentissement) ; le kit ne la note pas, l'interface du banc officiel est inconnue, non confirmée par Axel Durand-Allize. Les chiffres ne se transfèrent pas tels quels.
- Bonus `--verify` ignoré. Tableau de validation en direct : adresse et jeton des organisateurs encore inconnus.
- Mode de remise non confirmé : il faut remettre tout le dossier `handin/` (`fk/`, `routing.py`, `targets.py`, `deconflict.py` avec `planner.py`).

## Passage à l'échelle (bonus du brief, MESURÉ avec `fleet-kit/tools/scaling.py`)
L4 multiplié par 1, 2, 3, 4 (100 à 400 avions, 90 à 360 contacts, densité constante), 2 graines, exécution comme à l'évaluation (sous-processus). Tous les plans sont valides et plus hauts que le baseline du kit : L4 x1 875,8 et 765,4 contre 468,9 et 443,4 ; x2 623,4 et 594,9 contre 459,3 et 419,1 ; x3 229,6 et 462,6 contre 125,4 et 289,2 ; x4 510,2 et 622,4 contre 307,2 et 481,7. Le temps dépassait l'échéance interne avec la taille (38,2 s à 100 avions, 40,9 s à 200, 46,7 s à 300, 49,2 s à 400 : construction des routes et validation non interruptibles). Correctif : le budget diminue de 0,04 s par avion au-delà de 100 (aucun effet sur L1 à L4) ; mesuré ensuite : 400 avions en 35,2 s (497,1), 500 avions en 31,7 s (134,4), plans valides. Limite : au-delà de 500 avions rien n'est mesuré, et le score par avion chute (le planificateur ne couvre qu'une partie des contacts dans le temps imparti).

## Perte de liaison (optionnelle, MESURÉ dans notre simulateur : 8 scénarios L2 et L3, 30 tirages chacun)
Le plan remis n'est pas modifié. Le brief demande une politique de perte de liaison et une courbe de dimensionnement ; notre étude (détail et limites : `fleet-kit/linkloss/README.md`) donne :
- Un plan valide et très serré dans le temps casse dès que les avions dérivent : avec 10 % de ralentissement, 40 % des tirages violent la séparation de 40 m sur le plan remis.
- Planifier contre des règles plus strictes (séparation +40 m, marges de temps +10 s) avec le même planificateur donne un plan encore valide pour le vrai scénario, qui perd 19 % de score nominal (314,9 contre 387,2) mais gagne +9,6 % en score attendu à 10 % de dérive et +15 % à 30 %.
- La diffusion de retard entre équipiers (portée 1000 m, 3 messages) ajoute +3 % à +9 % à marge égale ; sans portée elle coûte ses messages et fait moins bien que continuer à l'aveugle. Un plan à marge tient sur un budget de communication serré (courbe presque plate dès 100 m), un plan sans marge non.
- Décision de remise : le plan remis reste celui sans marge (meilleur score nominal) ; le jeu de plans à marges est disponible (`linkloss/harden.py`) si les organisateurs notent la perte de liaison.

## Prochaines étapes
Le planner v7 est terminé côté code : l'ordre des contacts, le classement des hostiles infaisables, la politique de perte de liaison et la courbe de dimensionnement sont faits (voir plus bas). Pistes non mesurées, déjà préparées en fichiers désactivés : sauter les hostiles bloqués par R7 (`targets.py`, `PLANNER_TARGETS=1`), prix plus élevé des effecteurs light sur L4, décalage des décollages pour R8 (`deconflict.py`). Critère pour les garder : gain moyen positif sur au moins 20 graines de L4, au plus 40 % de graines moins bonnes, 0 invalide, plus de 1 % pour dépasser le bruit de rejeu.

## Résultats finaux du banc (planner v3, 50 graines par niveau, 200 cas)
MESURÉ : 200/200 valides, temps max 39,7 s. L1 5083,0 ; L2 12497,2 ; L3 23985,0 ; L4 41784,1 ; total 83349,3. Contre le baseline du kit sur les mêmes graines : L1 ×1,069 ; L2 ×1,098 ; L3 ×1,237 ; L4 ×1,597. Contre la v2 : +1,8 % au total.

## Résultats finaux du banc (planner v4, 50 graines par niveau, 200 cas, PLANNER_WORKERS=2)
MESURÉ (v4) : 200/200 valides, temps max 40,0 s. L1 5083,0 ; L2 12496,8 ; L3 23968,5 ; L4 44412,3 ; total 85960,6. Contre le baseline du kit sur les mêmes graines : L1 x1,069 ; L2 x1,098 ; L3 x1,236 ; L4 x1,698. Contre la v3 : total +3,1 %, L4 +6,3 % (36 graines mieux, 3 moins bien, pire -16,8 %), L1 à L3 inchangés au bruit près (le rejeu de la v3 varie de 0,1 à 0,25 % sur les sommes).
Origine du gain de la v4 : un essai de passe élargie sur un plan v3 de L4 a montré que les contacts gagnés l'étaient par des scouts de rang 7 à 14 par la distance, avec les options par défaut. La v3 n'essayait que les 6 plus proches.
Vérifications : check_handin 8/8 (total 3968,6 contre baseline 2748,6) ; tests de robustesse et link-loss 21/21 ; charge extrême (30 boucles en parallèle) 39,1 s valide (mesuré sur la v3) ; copie propre avec `env -i` valide ; passage à l'échelle valide jusqu'à 500 avions.

## Résultats finaux du banc (planner v5 = v4 + contrôle incrémental, 50 graines par niveau, 200 cas, PLANNER_WORKERS=2)
MESURÉ : 200/200 valides, temps max 39,2 s. L1 5083,0 ; L2 12497,2 ; L3 24089,6 ; L4 46301,3 ; total 87971,1. Contre le baseline du kit : L1 x1,069 ; L2 x1,098 ; L3 x1,242 ; L4 x1,770. Contre la v4 : total +2,3 %, L4 +4,25 % (29 graines mieux, 0 moins bien), L3 +0,5 % (10 mieux, 0 moins bien). Contre la v1 : total +11,0 % (79255,2 -> 87971,1).
Origine : le profil d'une construction L4 montrait 70 % du temps dans `evaluate` complet ; le score incrémental est égal à `evaluate` au millième sur 4 constructions testées, et la construction Routed de L4 passe de 35,7 s à 10,8 s (en v4 elle occupait presque tout le budget, donc la montée par relances n'avait pas lieu).
Vérifications v5 : check_handin 8/8 (total 3968,7) ; tests robustesse et link-loss 21/21 ; 1 seul cœur, L3 et L4 graines 0 à 7 : 4043,8 et 7116,8 (valides, 38,7 s max) ; passage à l'échelle valide à 300 et 400 avions (34,9 s et 30,1 s).

## Résultats finaux du banc (planner v6 = v5 + 15 scouts en options complètes + 3 délais d'arrivée d'effecteurs, 50 graines par niveau, PLANNER_WORKERS=2)
MESURÉ (L1 et L2 : banc de la variante finale ; L3 : 50 graines ; L4 : 50 graines) : 0 invalide, temps max 39,3 s. L1 5083,0 ; L2 12498,2 ; L3 24179,9 ; L4 50591,2 ; total 92352,3. Contre le baseline du kit (mêmes graines) : L1 x1,069 ; L2 x1,098 ; L3 x1,247 ; L4 x1,934 ; total x1,497. Contre la v5 : total +5,0 % ; contre la v1 de vendredi : +16,5 %.
Généralisation (graines 50 à 79, jamais utilisées pour régler) : 0 invalide sur les 60 cas L3 et L4, L3 14527,1 et L4 30351,6 (la v5 donnait 14446,0 et 27870,2, le baseline 11477,6 et 16266,5, soit L4 x1,87).
Ce qui a fait gagner, dans l'ordre : (1) tous les scouts en options complètes (L4 +6,6 %), (2) moins d'options d'arrivée d'effecteurs (0, 20, 90 s au lieu de 5 valeurs : L4 +2,5 %, les constructions plus rapides valent plus que les options en plus), (3) contrôle incrémental (L4 +4,25 %), (4) scouts lointains en second niveau (L4 +6,3 %). Variantes mesurées et rejetées : options élargies pour les scouts (angles, départs, rotations : -6 à -12 % sur L4), polissage final, reprise de préfixe.
Vérifications v6 : check_handin 8/8 (total 4173,7 contre baseline 2748,6), tests robustesse et link-loss 21/21, 1 seul cœur L3 4018,7 et L4 7829,1 sur les graines 0 à 7 (valides), copie propre avec `env -i` et 1 cœur valide (L4 graine 3 : 978,6 en 38,3 s), passage à l'échelle valide à 200, 300 et 400 avions (42,0 s au pire).

## Résultats finaux du banc (planner v7 = v6 + routage de l'équipe seul au-dessus de 20 avions, 50 graines par niveau, PLANNER_WORKERS=2)
MESURÉ : 0 invalide, temps max 39,6 s. L1 5083,0 ; L2 12498,2 ; L3 24332,0 ; L4 52665,4 ; total 94578,6. Contre le baseline du kit : L1 x1,069 ; L2 x1,098 ; L3 x1,254 ; L4 x2,013 ; total x1,533. Contre la v6 : L3 +0,63 %, L4 +4,10 %, total +2,4 % ; contre la v1 de vendredi : +19,3 %.
Généralisation (graines 50 à 79, jamais utilisées pour régler) : 0 invalide sur 60 cas, L3 14701,9 (x1,281 le baseline) et L4 31654,7 (x1,946 le baseline) ; la v6 donnait 14527,1 et 30351,6.
Pourquoi : sur L3 et L4 le routage de l'équipe bat celui du kit, et ne garder que lui donne plus de relances dans le même temps (L4 graines 0 à 15 : 16720,9 contre 16273,8 avec les deux routages, 14987,5 avec celui du kit seul). Sur L1 et L2 (12 avions ou moins) les deux routages sont gardés : le routage seul y coûtait 0,4 % sur L2. Si le module de routage plante, le planificateur retombe sur le routage du kit (test).
Vérifications v7 : voir PROGRESSION.md (tests, check_handin, 1 cœur).
Vérifications v7 : check_handin 8/8 (total 4226,5 contre baseline 2748,6) ; tests de robustesse (dont routage cassé, pool en échec, workers bloqués) et link-loss 22/22 ; 1 seul cœur, graines 0 à 7 : L3 4048,3 et L4 8080,4 (valides) ; plans d'exemple L4 graine 3 : 1076,7 (baseline 532,9), L3 graine 3 : 482,5.

## Planner sur main fusionné, puis saut des hostiles bloqués par R7 (MESURÉ le 2026-11-21)
Banc de `main` (commit 55327de, v7 avec le filet de l'équipe), 50 graines par niveau, copie propre comme le jury, PLANNER_WORKERS=2, 3 cas en parallèle : 0 invalide, temps max 38,6 s. L1 5083,0 ; L2 12536,4 ; L3 24449,3 ; L4 53467,6 ; total 95536,4 (baseline 61695,9, x1,549 ; L4 x2,044).
Où partent les essais sur L4 (graines 0 à 2, 30 s) : 67 à 89 % des essais d'effecteurs sont rejetés par R7 (hostile trop proche d'un ami ou d'un civil), donc perdus à coup sûr. `targets.skip` les saute, et le test est le même que `_r7` du validateur : aucun hostile servable n'est sauté. Activé par défaut (PLANNER_TARGETS=0 le coupe) : L4, 50 graines, graine par graine contre le banc ci-dessus, +1,27 % (53467,6 vers 54146,4 ; 25 graines meilleures, 25 identiques, 0 moins bonne ; écart moyen 13,6 pour une erreur type de 2,9) ; L3, 20 graines : +0,51 % (10 meilleures, 0 moins bonne) ; L1 et L2 identiques ; 0 invalide, temps max 38,5 s. `check_handin` : 4296,6 contre 4226,5 avant (baseline 2748,6), 0 échec. Suite de tests de l'équipe (pytest) : 150 tests OK. Journaux bruts : `docs/bench_logs/` du dépôt privé de Louis.
Pistes restantes mesurées : le départ des éclaireurs décalé de 3 à 100 s rendrait valides 43 à 58 % de leurs candidats rejetés par R8 (faisabilité seulement, gain en score non mesuré) ; le prix des effecteurs light n'est pas essayé.
