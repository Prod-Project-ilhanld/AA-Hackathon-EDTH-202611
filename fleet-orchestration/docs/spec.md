# Spécification autonome : Fleet Orchestration (Alta Ares, SUB-15)

Ce fichier suffit à reprendre le projet sans l'historique de conversation. Sources : le brief Alta Ares (3 pages), `fleet-kit/README.md`, `README.md`, code de `fleet-kit/fleetkit/`. Les mesures viennent de `fleet-kit/tools/bench.py` et de rapports d'équipe (section 6).

## 1. But
Un `fleet-kit/handin/planner.py` qui lit un scénario JSON et écrit un plan JSON, avec la plus grande somme de scores sur des scénarios cachés (mêmes règles, même score, même validateur).
Remise : dimanche 22 novembre 2026, midi. Le mode de remise n'est pas connu (à demander aux organisateurs).

## 2. Contrat d'exécution (officiel)
- Appel : `python3 planner.py scenario.json plan.json`, dans une copie propre du dossier, avec `fleetkit` importable.
- 60 s par scénario. Plantage, dépassement, absence de plan ou plan invalide : 0 pour ce scénario.
- Python 3.9+, bibliothèque standard seulement. Tout code supplémentaire est dans le dossier remis.
- Classement : somme des scores bruts ; égalité départagée par le temps total d'exécution.
- Le jury regarde aussi la solidité et la présentation (présentation : plus tard).

## 3. Problème
- Monde 3D en mètres locaux (x est, y nord, z haut), sol plat, temps en secondes, horizon 900 s (L2-7).
- Avions : scouts (observent, doivent rentrer et atterrir à leur base) et effecteurs light ou heavy (à sens unique : un engagement les consomme).
- Contacts : hostile (engageable, besoin de N light et M heavy, fenêtre de temps), unknown (observation seule), friendly et civilian (jamais approchés).
- Zones : cylindres interdits sous leur plafond `top_m`, survolables au-dessus.
- Plan : une route par avion utilisé, waypoints `{t,x,y,z}` avec `action` (`observe` ou `engage`), `target`, `dwell_s`. Le premier waypoint est la base ; la route d'un effecteur finit par son engagement.

## 4. Les dix règles (invalide si une seule est violée)
R1 forme (graine, ids, une route par avion, temps croissants, départ à la base, effecteur finit par engage). R2 cinématique (vitesses, altitude 30 à 150 m sauf montée, atterrissage, plongée finale). R3 énergie (batterie utilisable, scouts rentrent). R4 confirmation : observation d'un scout terminée au moins `confirm_margin_s` (10 s) avant l'engagement. R5 autorisation (seuls les effecteurs engagent, seulement des hostiles ; scouts observent hostile ou unknown). R6 exclusion (zones et rayon de protection 100 m autour des friendly et civilian). R7 collatéral (pas d'engagement d'un hostile à moins de 200 m d'un friendly ou civilian). R8 séparation 40 m en 3D, sauf effecteurs engageant le même contact près de lui. R9 fenêtres de temps. R10 tout ou rien : exactement les effecteurs requis, dans `sync_window_s` (20 s).
Paramètres (L2-7) : R_obs 150 m, obs_dwell 20 s, R_eng 25 m, exempt_radius 100 m. Tous dans le bloc `rules` du scénario, identiques pour tous.

## 5. Score
`score = somme des points des contacts servis - lambda_e (0,5) x énergie en Wh - c_eff (10) x effecteurs utilisés`.
Un hostile est servi s'il est engagé (valide). Un unknown est servi s'il est observé. Le bonus `--verify` (+25 % si un scout observe 10 à 120 s après la dernière frappe) a son propre tableau et ne compte pas au classement.
Conséquence : un contact qui demande beaucoup d'effecteurs pour peu de points peut avoir un gain net négatif (10 points par effecteur).

## 6. Mesures et observations (vérifié)
- Baseline glouton (graines 0 à 4, score moyen) : L1 96,9 ; L2 229,7 ; L3 405,0 ; L4 468,1. Part des points servis : 0,60 ; 0,73 ; 0,60 ; 0,23.
- Cause (profilage L4-1) : le baseline n'essaie que les 3 scouts les plus proches (`_scout_candidates(limit=3)`). L4-1 : 10/50 hostiles, 6/15 scouts utilisés, score 432,5. Avec tous les scouts : 789,7, mais 95 s. Le temps vient de `evaluate` appelé à chaque essai (4 855 appels, 5 ms chacun ; R8 : 12,4 s ; R6 : 6,4 s sur 24,9 s avec 6 scouts).
- Rapport d'un coéquipier, L4 graine 3, glouton 532,9 : 18 contacts servis ; 27 heavy, 23 light et 9 scouts sur 15 restent au sol ; 6 scouts utilisés ; environ 2 115 points non servis sans blocage évident, hors R7 et hors drones épuisés (à vérifier : fenêtre, énergie, séparation). 11 hostiles environ sont interdits par R7. Les scouts utilisés ont consommé 26 à 35 Wh sur 30 à 44 Wh utilisables : l'énergie scout est un second plafond. Une observation peut confirmer plusieurs engagements du même contact. Ces chiffres sont rapportés par le coéquipier et recoupent la mesure L4-1 ci-dessus ; ils n'ont pas été rejoués.
- Un autre coéquipier : piste "scouts au sol" non vérifiée, à clarifier.

## 7. Approche retenue (hypothèse à valider par mesure)
1. Réutiliser le routage du baseline (détours de zones, couches d'altitude) : il produit des routes valides.
2. Candidats scouts élargis (tous), avec présélection bon marché avant validation complète : fenêtre atteignable, énergie, distance.
3. Validation incrémentale : ne tester que les paires d'avions concernées par l'ajout (R8, R6 locaux), puis une validation complète finale seulement sur le plan retenu.
4. Ne pas abandonner un contact au premier échec : essayer d'autres scouts, autres couches d'altitude, autres délais, autres angles.
5. Relances randomisées (ordre des contacts, gain net par effecteur) sous budget de 40 s, en gardant le meilleur plan valide ; repli sur le glouton si tout échoue.
6. Garde-fou : tout plan écrit est revalidé par `fleetkit.scorer.evaluate` ; si invalide, on écrit le dernier plan valide.

## 8. Perte de liaison (optionnelle)
Réponse trouvée dans les documents : le kit ne la simule pas (README : "no communication") et son scorer ne la note pas. Le brief papier la décrit comme seconde partie optionnelle (politique continue / hold / return / ajustement, diffusion à portée limitée avec cap de temps d'antenne, pertes et latence ; score = points servis après la coupure, sans violation, moins un coût par message ; courbe de dimensionnement sur le budget de com). Non confirmé par Axel Durand-Allize. Décision : après un planificateur solide, avec un mini-simulateur à nous. Idée centrale : un plan valide à trajets déjà séparés dans le temps tient sans radio ; la radio ne sert qu'aux écarts.

## 9. Critères de réussite
- C1 : 0 plan invalide, 0 plantage, 0 dépassement sur 50 graines par niveau (L1 à L4).
- C2 : temps maximal inférieur à 45 s par scénario (budget interne visé 40 s).
- C3 : score total supérieur au baseline sur chaque niveau ; objectif indicatif L4 : au moins 1,5 fois le baseline (L4-1 : 790 est atteignable en 95 s).
- C4 : `python3 handin/check_handin.py` passe depuis une copie propre.
- C5 (optionnel) : politique de perte de liaison + courbe de dimensionnement.

## 10. Commandes (depuis `fleet-kit/`)
```
python3 -m fleetkit generate L4 3 -o scenario.json
python3 -m fleetkit validate scenario.json plan.json
python3 -m fleetkit score scenario.json plan.json
python3 -m fleetkit view scenario.json plan.json --open
python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-9      # compare handin/planner.py au baseline
python3 handin/check_handin.py
```
