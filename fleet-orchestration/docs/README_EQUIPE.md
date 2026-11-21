# Fleet Orchestration : livrable d'équipe (EDTH x Adopt AI, Alta Ares SUB-15)

Brouillon du 2026-11-20. Les chiffres marqués MESURÉ viennent de `fleet-kit/tools/bench.py` ; ceux marqués À MESURER ne sont pas encore connus. Aucun chiffre n'est inventé.

## Problème
Une flotte mixte (scouts qui observent et rentrent, effecteurs à sens unique) doit servir des contacts sous dix règles (séparation 40 m, zones interdites, confirmation avant engagement, fenêtres de temps, tout ou rien, énergie). Un plan invalide vaut 0. Le jury note la somme des scores sur des scénarios cachés, puis la solidité et la présentation.

## Solution (planificateur de Louis, `fleet-kit/handin/planner.py`)
Glouton du kit élargi et rendu rapide :
- les 6 scouts les plus proches de chaque hostile avec toutes les options (le baseline en essaie 3), puis tous les autres scouts avec les options simples : sur L4 les scouts proches sont saturés pendant que d'autres restent au sol (v4) ;
- préfiltre bon marché (routes touchées seules, séparation R8 contre les autres) avant la validation complète du kit ;
- relances de l'ordre des contacts (points par effecteur requis, puis petites variations autour du meilleur ordre) pendant 38 s, sur plusieurs processus, avec deux routages : celui du kit et le module de routage 3D de l'équipe (`handin/routing.py`, 7thwardlord1) ; on garde le meilleur plan valide ;
- chaque pas accepté a passé `evaluate`, le plan final est revalidé, repli sur le meilleur plan valide.

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
| Louis | kit lu, baseline mesuré, banc 50 graines, planner v1 à v3 (avec le routage de l'équipe), tests de robustesse, mini-simulateur link-loss et courbe de dimensionnement, étude de passage à l'échelle | derniers réglages, démo |
| Swann | démo `swann_demo.py` (calques du viewer, rapport d'explication), rapport L4 graine 3 (glouton 532,9) | rapport d'explication sur les plans du moteur (branche `feature/planner-v1`) |
| Ilhan | accès au repo d'équipe, piste « scouts au sol » | à clarifier |
| 3 autres membres | non communiqué | à renseigner |

## Lancement en une commande
```sh
cd fleet-kit && python3 handin/check_handin.py
```
Un scénario à la main : `python3 -m fleetkit generate L4 3 -o scenario.json && python3 handin/planner.py scenario.json plan.json && python3 -m fleetkit view scenario.json plan.json --open`

## Script de démo, 2 minutes (à jouer avec les chiffres du banc)
1. Accroche (15 s) : un plan invalide vaut 0, donc la sécurité passe avant le score.
2. Moment fort (60 s) : même scénario L4 graine 3, baseline 532,9 contre notre plan v4 904,3, soit +70 % (MESURÉ, un seul scénario), dans le viewer ; montrer pourquoi tel hostile est servi et tel autre refusé (R7, horizon, énergie), avec le rapport de Swann.
3. Preuve (30 s) : sortie de `bench.py` sur 50 graines par niveau : 0 invalide, temps maximal 40,0 s (v4, MESURÉ).
4. Fermeture (15 s) : limites et suite.

## Limites connues
- Heuristique gloutonne avec relances, pas d'optimum prouvé ; aucune borne supérieure calculée.
- Utilise toujours 38 s, même sur L1 (ne change que les égalités de temps).
- Les versions 2 à 4 profitent de plusieurs cœurs ; à 1 cœur la v4 reste au-dessus de la v3 sur L4 (graines 0 à 7 : 6940,9 contre 6273,6 pour la v3 à 2 cœurs).
- Sur L4 graine 3, 10 hostiles sont interdits par R7 et plusieurs autres sont hors d'atteinte (aller-retour au-delà de 900 s) : le plafond réel est plus bas que le total des points.
- Perte de liaison : modélisée dans NOTRE simulateur (une seule perturbation, le ralentissement) ; le kit ne la note pas, l'interface du banc officiel est inconnue, non confirmée par Axel Durand-Allize. Les chiffres ne se transfèrent pas tels quels.
- Bonus `--verify` ignoré. Tableau de validation en direct : adresse et jeton des organisateurs encore inconnus.
- Mode de remise non confirmé.

## Passage à l'échelle (bonus du brief, MESURÉ avec `fleet-kit/tools/scaling.py`)
L4 multiplié par 1, 2, 3, 4 (100 à 400 avions, 90 à 360 contacts, densité constante), 2 graines, exécution comme à l'évaluation (sous-processus). Tous les plans sont valides et plus hauts que le baseline du kit : L4 x1 875,8 et 765,4 contre 468,9 et 443,4 ; x2 623,4 et 594,9 contre 459,3 et 419,1 ; x3 229,6 et 462,6 contre 125,4 et 289,2 ; x4 510,2 et 622,4 contre 307,2 et 481,7. Le temps dépassait l'échéance interne avec la taille (38,2 s à 100 avions, 40,9 s à 200, 46,7 s à 300, 49,2 s à 400 : construction des routes et validation non interruptibles). Correctif : le budget diminue de 0,04 s par avion au-delà de 100 (aucun effet sur L1 à L4) ; mesuré ensuite : 400 avions en 35,2 s (497,1), 500 avions en 31,7 s (134,4), plans valides. Limite : au-delà de 500 avions rien n'est mesuré, et le score par avion chute (le planificateur ne couvre qu'une partie des contacts dans le temps imparti).

## Perte de liaison (optionnelle, MESURÉ dans notre simulateur : 8 scénarios L2 et L3, 30 tirages chacun)
Le plan remis n'est pas modifié. Le brief demande une politique de perte de liaison et une courbe de dimensionnement ; notre étude (détail et limites : `fleet-kit/linkloss/README.md`) donne :
- Un plan valide et très serré dans le temps casse dès que les avions dérivent : avec 10 % de ralentissement, 40 % des tirages violent la séparation de 40 m sur le plan remis.
- Planifier contre des règles plus strictes (séparation +40 m, marges de temps +10 s) avec le même planificateur donne un plan encore valide pour le vrai scénario, qui perd 19 % de score nominal (314,9 contre 387,2) mais gagne +9,6 % en score attendu à 10 % de dérive et +15 % à 30 %.
- La diffusion de retard entre équipiers (portée 1000 m, 3 messages) ajoute +3 % à +9 % à marge égale ; sans portée elle coûte ses messages et fait moins bien que continuer à l'aveugle. Un plan à marge tient sur un budget de communication serré (courbe presque plate dès 100 m), un plan sans marge non.
- Décision de remise : le plan remis reste celui sans marge (meilleur score nominal) ; le jeu de plans à marges est disponible (`linkloss/harden.py`) si les organisateurs notent la perte de liaison.

## Prochaines étapes
Améliorer l'ordre des contacts (points par effecteur), classer les contacts réellement infeasibles, politique de perte de liaison avec mini-simulateur, courbe de dimensionnement.

## Résultats finaux du banc (planner v3, 50 graines par niveau, 200 cas)
MESURÉ : 200/200 valides, temps max 39,7 s. L1 5083,0 ; L2 12497,2 ; L3 23985,0 ; L4 41784,1 ; total 83349,3. Contre le baseline du kit sur les mêmes graines : L1 ×1,069 ; L2 ×1,098 ; L3 ×1,237 ; L4 ×1,597. Contre la v2 : +1,8 % au total.

## Résultats finaux du banc (planner v4, 50 graines par niveau, 200 cas, PLANNER_WORKERS=2)
MESURÉ : 200/200 valides, temps max 40,0 s. L1 5083,0 ; L2 12496,8 ; L3 23968,5 ; L4 44412,3 ; total 85960,6. Contre le baseline du kit sur les mêmes graines : L1 x1,069 ; L2 x1,098 ; L3 x1,236 ; L4 x1,698. Contre la v3 : total +3,1 %, L4 +6,3 % (36 graines mieux, 3 moins bien, pire -16,8 %), L1 à L3 inchangés au bruit près (le rejeu de la v3 varie de 0,1 à 0,25 % sur les sommes).
Origine du gain de la v4 : un essai de passe élargie sur un plan v3 de L4 a montré que les contacts gagnés l'étaient par des scouts de rang 7 à 14 par la distance, avec les options par défaut. La v3 n'essayait que les 6 plus proches.
Vérifications : check_handin 8/8 (total 3968,6 contre baseline 2748,6) ; tests de robustesse et link-loss 21/21 ; charge extrême (30 boucles en parallèle) 39,1 s valide (mesuré sur la v3) ; copie propre avec `env -i` valide ; passage à l'échelle valide jusqu'à 500 avions.
