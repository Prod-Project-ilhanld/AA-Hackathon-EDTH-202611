# Démo et explication (binôme 3, Swann)

Trois outils, bibliothèque standard uniquement, qui comparent n'importe quel plan au glouton du kit
et expliquent le résultat pour le jury.

## Lancer (depuis `fleet-kit/`)

```
python demo/swann_demo.py <scenario.json> [plan.json] -o <dossier_sortie>
```

Sans `plan.json` : compare le glouton à lui-même (test de fumée). Avec un plan : compare notre plan
au glouton et produit, dans `<dossier_sortie>/` :
- `view.html` — le visualiseur du kit, avec des calques en plus : Gagnés / Perdus / À gagner /
  Bloqués par rapport au glouton, et la raison de chaque contact non servi.
- `explication.md` — tableau de score, stratégie du planificateur (si notre plan gagne), ressources
  utilisées, affectation drone par drone, contacts non servis et pourquoi. La section stratégie
  décrit `planner v2` (Louis) ; à revérifier avec lui avant le pitch si l'approche change encore.

```
python demo/marge_glouton.py --levels L3 L4 --seeds 0-9 --csv marge.csv
```

Marge laissée par le glouton sur plusieurs seeds (slide « le problème » du pitch).

```
python demo/gen_script_demo.py <scenario.json> <plan.json>
```

Régénère `SCRIPT_DEMO.md` à partir de `SCRIPT_DEMO.template.md` avec les vrais chiffres mesurés sur
ce scénario/plan (score, gain, points réellement gagnables). À relancer à chaque nouveau plan —
ne jamais recopier les chiffres à la main.

## Résultat de référence

Scénario L4 seed 3 (100 drones, 70 contacts servables), plan `planner v7` de Louis (fusionné dans
`main`, PR #2) contre le glouton du kit : **532,9 → 1076,7 pts, +102 %, plan valide** sur les 10
règles, 37 contacts servis contre 18. Un seul scénario — le chiffre solide est le banc de Louis :
50 graines par niveau, scénarios du kit, **94 578,6 pts contre 61 695,9 pour le glouton (x1,53
global, x2,0 sur L4)**, 0 plan invalide, 39,6 s au maximum. Reproductible depuis `fleet-kit/` :

```
python -m fleetkit generate L4 3 -o s_l4.json
git show origin/main:fleet-orchestration/fleet-kit/examples/plans/L4-seed3.plan.json > plan_l4_louis.json
python demo/swann_demo.py s_l4.json plan_l4_louis.json -o demo_l4_louis_v7
```

## Diagnostic des contacts non servis

`diagnose()` vérifie d'abord R7 (collatéral). Si `handin/planner.py` (le vrai planificateur de
Louis) est présent sur le disque, il rejoue ensuite le **vrai routage** sur le contact seul
(`FastPlanner.serve_hostile`/`serve_unknown`), avec un budget de temps par contact
(`DIAG_BUDGET_S`, 8 s par défaut) : trois verdicts possibles, « à gagner » (routable avec des drones
encore au sol, sans conflit), « en concurrence » (routable seul, mais les drones nécessaires sont
déjà pris par un autre contact de notre plan) ou « hors de portée » (aucun routage trouvé même avec
tous les drones disponibles). Limite connue : le test par contact est budgété en temps ; sous forte
charge machine, quelques contacts limites basculent sur l'estimation en ligne directe (ci-dessous),
ce qui fait varier le total « à gagner » de quelques dizaines de points d'un lancement à l'autre.

Si `handin/planner.py` n'est pas sur le disque (cas normal sur cette branche, le code de Louis
n'étant pas fusionné ici), `diagnose()` retombe sur une borne optimiste par trajet direct : ne
vérifie ni R6 (détour de zones), ni R8 (séparation), ni R10 (synchronisation entre effecteurs). Le
rapport l'indique explicitement dans chaque ligne concernée.

## Prochaines étapes

- Scénario de démo final tranché avec Ilhan et Mahmoud : **L4 graine 3** (déjà la référence
  ci-dessus, vidéo de secours et script alignés dessus).
- Rejouer sur les scénarios de la grille publique (L1-101 à L4-402) dès qu'ils sont disponibles.
- Script de démo minuté : voir `SCRIPT_DEMO.md` (régénéré par `gen_script_demo.py`).
