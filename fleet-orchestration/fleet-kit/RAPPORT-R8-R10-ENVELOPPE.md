# Vérification R8 / R10 / enveloppe anti-zéro du planner (Martin)

Cible : `handin/planner.py` de la branche `feature/planner-v1`, commit `e604228` (v7, Louis).
Aucune modification de `planner.py` : ce document et les tests ne font que vérifier.

## Méthode

Le planner n'appelle pas le validateur complet à chaque essai : `_try` valide seulement les routes touchées
et compare en R8 au reste du plan. Les tests forcent des violations directement sur `_try` et comparent
son verdict au validateur complet du kit (l'oracle). Deux propriétés :

- solidité : si `_try` accepte, le validateur complet doit accepter ;
- rejet : les cas qui violent R8 ou R10 doivent être refusés.

Lancer depuis `fleet-kit/` : `python3 tests/test_planner_r8_r10.py` et `python3 tests/test_planner_envelope.py`.

## R8 — séparation (12 tests au total avec R10, 11 passent, 1 échec attendu documenté plus bas)

Tous les cas R8 sont rejetés correctement : routes à 0,5 / 20 / 39,9 m, deux routes nouvelles dans le même essai,
croisement en vol. La limite exacte de 40 m est acceptée, 39,9 m refusée, un décollage décalé légitime
est accepté (le planner n'est pas trop strict), et une route remplacée n'est pas comparée à son ancienne version.

## R10 — engagement synchronisé tout-ou-rien

Rejetés correctement : écart de synchronisation supérieur à 20 s, effecteur manquant, effecteur en trop,
engagement à plus de 25 m du contact. Sur C04 (1 léger + 1 lourd) : écart 25 s et 60 s rejetés (R10),
écart 20,1 s rejeté (R10 et R8 ensemble). Les écarts 5 / 19,9 / 20 s sont rejetés à cause de R8
(géométrie des pistes de décollage), pas de R10, et le validateur complet est du même avis.

### Faille latente : R10 n'est pas vérifié entre deux essais

`_try` documente que R8 est la seule règle qui couple les routes. R10 les couple aussi (nombre d'effecteurs
et fenêtre de 20 s par contact).

Scénario : C01 a besoin d'un seul léger. L01 l'engage et est commité. Dans un second essai, `extra` contient
la route du scout et celle de L02 vers C01 (arrivée 2 s après L01, couche 40 m). `_try` accepte
(score -11,46) alors que le validateur complet dit R10 seul.

Mesure : sur 105 variantes (décalage 0 à 40 s, 3 couches, 5 angles), 73 sont invalides en R10 seul, et `_try`
en accepte à tort.
Atteignable aujourd'hui : non, `build` sert chaque contact une seule fois et le garde final `evaluate` écarte
un plan invalide. Atteignable après une boucle de réparation ou un second passage sur un contact.
Non corrigé ici : à discuter avec Louis. Le test est marqué `expectedFailure` et passera en
« unexpected success » quand la faille sera corrigée.

## Enveloppe anti-zéro

Niveaux de `try/except` présents : par contact, par construction, par worker, création du pool, garde final
(`evaluate`) et `main`. Un test neutralise exprès le filtre incrémental (L2, graine 0, budget 10 s, 1 worker) :
le planner écrit un plan valide de 293,1 contre 281,3 pour la baseline du kit, car chaque construction est
re-validée et seules les valides sont gardées.

Lacune structurelle : `greedy_plan` du kit n'est appelé nulle part. Si toutes les constructions échouaient,
le plan écrit serait vide (score 0). Je n'ai pas réussi à le provoquer, donc c'est une lacune de conception,
pas un bug observé. Test marqué `expectedFailure`.

Limite à surveiller : `_place_effectors` décale les effecteurs de 5 s fixes. Pire cas sur L1 à L4 × 50 graines :
4 effecteurs, soit 15 s, sous la fenêtre de 20 s. Une fenêtre durcie (`linkloss/harden.py` réduit
`sync_window_s`) rendrait certains contacts inservables.

## check_handin.py sur e604228

8/8 ok, 0 échec. Total 4229,6 contre 2748,6 pour la baseline. Temps maximum 38,1 s (limite 60 s), mesuré sur
une machine de 20 cœurs, le planner utilisant jusqu'à 8 workers.

| Scénario | Score | Baseline | Temps |
|---|---|---|---|
| L1-0 | 125,8 | 123,8 | 12,4 s |
| L1-1 | 72,0 | 68,8 | 12,2 s |
| L2-0 | 293,8 | 281,3 | 38,1 s |
| L2-1 | 349,3 | 338,9 | 38,1 s |
| L3-0 | 608,0 | 449,1 | 38,1 s |
| L3-1 | 514,0 | 463,9 | 38,1 s |
| L4-0 | 1137,8 | 590,3 | 38,1 s |
| L4-1 | 1129,0 | 432,5 | 38,1 s |

Seules les graines 0 et 1 ont été lancées : ce n'est pas comparable aux 50 graines mesurées par Louis.

## Avec plus de temps

- relancer `check_handin.py` sur plusieurs graines et sur une machine à moins de cœurs pour confirmer la marge de temps ;
- proposer à Louis un correctif de R10 inter-essais et un repli sur `greedy_plan` ;
- tester une fenêtre de synchronisation réduite (version durcie).
