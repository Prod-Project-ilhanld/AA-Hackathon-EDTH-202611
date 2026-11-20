# Démo et explication (binôme 3, Swann)

Deux outils, bibliothèque standard uniquement, qui comparent n'importe quel plan au glouton du kit
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
  décrit `planner v1` (Louis) ; à revérifier avec lui avant le pitch si une v2 a changé l'approche.

```
python demo/marge_glouton.py --levels L3 L4 --seeds 0-9 --csv marge.csv
```

Marge laissée par le glouton sur plusieurs seeds (slide « le problème » du pitch).

## Résultat de référence

Scénario L4 seed 3 (100 drones, 70 contacts), plan `planner v1` de Louis contre le glouton du kit :
**532,9 → 763,9 pts, +43 %, plan valide** sur les 10 règles. Un seul scénario — le banc multi-seed
est tenu par Mahmoud (`tools/bench.py`). Reproductible depuis `fleet-kit/` :

```
python -m fleetkit generate L4 3 -o s_l4.json
git show origin/feature/planner-v1:fleet-orchestration/fleet-kit/examples/plans/L4-seed3.plan.json > plan_l4_louis.json
python demo/swann_demo.py s_l4.json plan_l4_louis.json -o demo_l4_louis_v1
```

## Limites connues

`diagnose()` vérifie R7 (collatéral), la disponibilité des drones, et pour chaque drone encore au
sol si un trajet **direct** tient dans la fenêtre de temps et la batterie. Il ne vérifie pas R6
(détour autour des zones), R8 (séparation entre drones en vol) ni R10 (synchronisation entre
effecteurs) : un contact marqué « à gagner » peut donc rester bloqué pour l'une de ces trois raisons
une fois la vraie trajectoire calculée. C'est une borne optimiste, pas un plafond garanti.

## Prochaines étapes

- Rejouer sur les scénarios de la grille publique (L1-101 à L4-402) dès qu'ils sont disponibles.
- Choisir avec Ilhan et Mahmoud le scénario de démo final (probablement un L4 à fort gain).
- Script de démo minuté : voir `SCRIPT_DEMO.md`.
