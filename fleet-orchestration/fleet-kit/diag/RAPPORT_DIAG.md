# Diagnostic des pires graines shift et mesure de scouts.py

Martin, 21/11/2026, sur `main` à jour (`5dbc69a` ; `handin/` identique à `717535a`, ordonnanceur R8 actif). Rien n'a été modifié dans `handin/`, `scouts.py` ni `params.py`.

## 1. Diagnostic des pires graines

`tools/shift.py --variants S-half-scouts S-battery --seeds 0-49`, budget 38 s, `/usr/bin/python3`, un processus par variante (8 workers chacun, en parallèle). 100 runs, 0 échec.

| Variante | Total | Baseline | Ratio | Part de borne (total) | Part médiane par graine | Temps max |
|---|---|---|---|---|---|---|
| S-battery | 37860,9 | 16518,1 | ×2,29 | 61,3 % | 63,8 % | 39,5 s |
| S-half-scouts | 48536,6 | 25680,7 | ×1,89 | 62,4 % | 62,5 % | 39,4 s |

Ça recoupe tes 60 %. Part de borne = score du planner / `bound.bound(scenario)`, variante enregistrée dans `generator.LEVELS` comme dans `shift.py`.

### Les 3 pires graines par variante

| Graine | Part de borne | Score / borne | Hostiles non servis | Inconnus non servis |
|---|---|---|---|---|
| S-battery 24 | 31,8 % | 428,6 / 1348,5 | 36 / 50 (2647 pts) | 16 / 20 (323 pts) |
| S-battery 7 | 36,4 % | 317,1 / 869,8 | 45 / 50 (3289 pts) | 10 / 20 (207 pts) |
| S-battery 17 | 37,6 % | 407,0 / 1081,1 | 43 / 50 (2938 pts) | 10 / 20 (154 pts) |
| S-half-scouts 10 | 41,1 % | 522,2 / 1271,6 | 34 / 50 (2201 pts) | 18 / 20 (353 pts) |
| S-half-scouts 3 | 48,1 % | 679,0 / 1411,2 | 33 / 50 (2383 pts) | 11 / 20 (178 pts) |
| S-half-scouts 0 | 48,4 % | 685,7 / 1417,9 | 32 / 50 (2237 pts) | 15 / 20 (307 pts) |

Rapports de Swann : `diag/diag_<variante>_<graine>/explication.md`, généré avec le vrai routage du planner (`PYTHONPATH` sur `handin/`), aucun « budget de test dépassé ». Chaque dossier garde aussi `scenario.json` et `plan.json`. Le visualiseur `view.html` (~0,8 Mo) n'est pas versionné ; pour le régénérer, depuis `fleet-kit/` : `for d in diag/diag_S-*/; do PYTHONPATH=.:handin python3 demo/swann_demo.py "$d/scenario.json" "$d/plan.json" -o "$d"; done` (réécrit aussi `explication.md`). Détail par contact : `diag/worst_S-battery.md` et `diag/worst_S-half-scouts.md`.

### Pourquoi, d'après explication.md

`explication.md` classe chaque contact non servi en trois cas : R7, à gagner (routable seul avec des drones encore au sol), ou aucun routage trouvé même avec tous les drones libres. Il ne distingue pas portée, énergie et fenêtre. J'ai donc ajouté un contrôle statique en ligne droite, avec les mêmes formules que `tools/bound.py` : fenêtre trop courte pour un éclaireur, batterie d'éclaireur insuffisante, effecteurs trop loin ou sans batterie. Les contacts que ce contrôle déclare faisables en ligne droite sont classés « faisable en ligne droite ». Le contrôle ne sait pas séparer R8, R10 ni le temps partagé des éclaireurs.

Somme sur les 3 pires graines de chaque variante :

| Raison | S-battery | S-half-scouts |
|---|---|---|
| R7 (hostiles) | 33 (2554 pts) | 33 (2457 pts) |
| Éclaireur, énergie : aucun n'a la batterie pour l'aller-retour (hostiles) | 30 (2123 pts) | 6 (385 pts) |
| Éclaireur, fenêtre : aucun n'arrive à temps (hostiles) | 12 (810 pts) | 12 (771 pts) |
| Faisable en ligne droite, mais le vrai routage échoue même avec tous les drones libres (hostiles) | 45 (3052 pts) | 37 (2456 pts) |
| À gagner selon Swann (hostiles) | 4 (335 pts) | 10 (684 pts) |
| À gagner selon Swann (inconnus) | 15 (296 pts) | 28 (606 pts) |
| Inconnus hors d'atteinte (énergie, fenêtre, routage) | 21 (388 pts) | 16 (232 pts) |
| En concurrence avec un contact déjà servi (Swann) | 0 | 1 (68 pts) |

Aucune graine n'a d'effecteur trop loin ou sans batterie : les effecteurs ne sont jamais le facteur limitant.

### Lecture

- **R7** pèse beaucoup en points, mais la borne exclut déjà ces hostiles. Il n'explique donc pas l'écart à la borne.
- **S-battery : l'énergie des éclaireurs est bien le goulot.** 30 hostiles (2123 pts) n'ont aucun éclaireur capable de faire l'aller-retour. Ça confirme ta lecture « rareté ».
- **Le plus gros poste dans les deux variantes : faisable en ligne droite, mais introuvable par le vrai routage.** 45 et 37 hostiles. C'est l'écart entre la borne (ligne droite, sans R6, R8, R10, sans montée) et le routage réel : détours de zones, énergie réelle, synchronisation, espacement R8. Une partie de l'écart de 40 % est donc la borne qui est lâche, pas des points perdus.
- **Points laissés sur la table selon Swann.** Sur S-half-scouts : 10 hostiles (684 pts) et 28 inconnus (606 pts) routables seuls avec des drones encore au sol. Réserve : ce test rejoue le contact seul, sans le reste du plan. Il ne vérifie pas R8 contre les routes déjà prises, donc c'est optimiste. C'est la cible naturelle de `scouts.py`, mais la mesure ci-dessous ne montre aucun gain dessus.

## 2. Mesure de scouts.py (PLANNER_SCOUTS=1)

`FLEET_ITERS=1 PLANNER_WORKERS=2`, `tools/bench.py --base ""`, graines 0 à 19, avec et sans `PLANNER_SCOUTS=1`. Pour S-half-scouts, la variante est enregistrée dans `LEVELS` par `diag/bench_variant.py`, comme dans `shift.py`. 80 runs, 0 invalide.

| | Total sans | Total avec | Écart | Gain moyen par graine | Meilleures / égales / moins bonnes | Invalides |
|---|---|---|---|---|---|---|
| L4 (décision) | 21395,5 | 21421,7 | +0,12 % | +1,31 ± 1,31 | 1 / 19 / 0 | 0 |
| S-half-scouts (contrôle) | 17319,5 | 17319,5 | 0,00 % | 0 | 0 / 20 / 0 | 0 |

**Règle d'activation : formellement elle passe** (gain moyen > 0, 0 % de graines moins bonnes, 0 invalide). **Mais le gain vient d'une seule graine** (L4 graine 17, +26,2) : l'erreur standard égale la moyenne, ce n'est pas un effet mesurable. Sur S-half-scouts, où les éclaireurs sont rares, il ne change rien.

J'ai vérifié que ce n'est pas une panne silencieuse : `planner.py` avale toute exception de `scouts.sweep_unknowns`. Appelé directement (`diag/scouts_probe.py`), il tourne sans erreur et ajoute 0 ou 1 inconnu par construction (L4 graines 0 et 17, S-half-scouts graine 0).

Limite : L4 graine 12 a atteint le budget de 38 s dans les deux modes. Pour cette graine, le plan peut dépendre du temps machine. Elle a donné le même score dans les deux.

**Je n'ai rien activé.** C'est le fichier d'Ilhan, la décision te revient.

## 3.

Ton message annonçait trois choses, je n'en ai reçu que deux. Envoie-moi la troisième.

## Fichiers (dans `diag/`, non commités)

`shift2_battery.json`, `shift2_half.json` (runs), `shares_<variante>.csv` (part de borne par graine), `worst_<variante>.md`, `diag_<variante>_<graine>/` (scénario, plan, rapport de Swann), `scouts_*.json` (bancs), `worst.py`, `bench_variant.py`, `paired.py`, `scouts_probe.py`.
