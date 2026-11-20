# Script de démo (2 minutes) — Fleet Orchestration

À adapter au scénario choisi avec l'équipe avant le pitch ; les chiffres ci-dessous sont ceux
mesurés sur L4 seed 3 (100 drones, 70 contacts), à remplacer par ceux du scénario final.

## Accroche (20 s)

« Le kit fournit un glouton de référence. Sur ce scénario L4, il sert 18 contacts sur 70 pour un
score de 532,9 — et laisse 1 830 points sur la table rien qu'en comptant ceux qu'un drone encore au
sol pourrait atteindre en ligne droite, fenêtre et batterie comprises. »

## Moment fort (60 s)

1. Ouvrir `view.html` du plan final, calque **Gagnés vs glouton** activé (vert).
   « Notre planificateur élargit la recherche à tous les éclaireurs disponibles, pas seulement les
   trois plus proches, et relance plusieurs fois sous un budget de temps. »
2. Ouvrir `explication.md`, section **Contacts non servis**.
   Montrer un contact bloqué par R7 (collatéral) et un autre marqué « à gagner ».
   « On sait exactement pourquoi chaque contact est pris ou non — pas seulement que le score est
   plus bas. »

## Preuve chiffrée (30 s)

« Résultat mesuré, pas estimé : glouton 532,9 → notre plan 763,9 points, **+43 %**, plan valide sur
les 10 règles. » (Afficher le tableau de score en haut de `explication.md`.)

## Clôture (10 s)

« Le même pipeline tourne sur n'importe quel plan et n'importe quel scénario en une commande — on
peut le rejouer en direct si le jury veut changer de scénario. »

## Limites à assumer si on nous les demande

- Pas de politique de perte de liaison : non publiée par les organisateurs au moment du rendu.
- Le diagnostic « à gagner » est une borne optimiste (trajet direct) : il ne garantit pas R6
  (détour de zones), R8 (séparation) ni R10 (synchronisation entre effecteurs).
- +43 % mesuré sur un seul scénario (L4 seed 3). Le banc multi-seed est tenu par Mahmoud.

## Vidéo de secours

À enregistrer avant dimanche 9h (gel du code) : rejouer exactement ce script sur le scénario de
démo final, écran `view.html` + `explication.md` ouverts côte à côte, sans narration improvisée.
