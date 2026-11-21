# Script de démo (2 minutes) — Fleet Orchestration

À adapter au scénario choisi avec l'équipe avant le pitch. Chiffres générés par
`python demo/gen_script_demo.py` sur L4 seed 3 — ne pas les recopier à la main,
relancer le générateur à chaque nouveau plan.

## Accroche (20 s)

« Le kit fournit un glouton de référence. Sur ce scénario L4, il sert 18 contacts
sur 70 pour un score de 532,9 — et laisse 1223 points sur
la table rien qu'en rejouant le vrai routage sur chacun des contacts qu'il manque. »

## Moment fort (60 s)

1. Ouvrir `view.html` du plan final, calque **Gagnés vs glouton** activé (vert).
   « Notre planificateur teste 15 éclaireurs par contact hostile avec toutes leurs options, trie
   les contacts par points par effecteur requis, et relance plusieurs fois sous un budget de
   temps, réparti sur plusieurs processeurs. »
2. Ouvrir `explication.md`, section **Contacts non servis**.
   Montrer un contact bloqué par R7 (collatéral), un contact « hors de portée même avec tous les
   drones disponibles » (routage réel testé, pas une estimation), et si possible un contact
   « en concurrence » pour les mêmes drones.
   « On ne devine pas : chaque verdict vient d'un vrai essai de routage sur ce contact, pas d'une
   ligne droite optimiste. »

## Preuve chiffrée (30 s)

« Résultat mesuré, pas estimé : glouton 532,9 → notre plan 1076,7 points,
**+102 %**, plan valide sur les 10 règles, 37 contacts servis contre
18. » (Afficher le tableau de score en haut de `explication.md`.)

## Clôture (10 s)

« Le même pipeline tourne sur n'importe quel plan et n'importe quel scénario en une commande — on
peut le rejouer en direct si le jury veut changer de scénario. »

## Limites à assumer si on nous les demande

- Perte de liaison : publiée par les organisateurs comme second rendu optionnel, scoré
  séparément (ne change pas le classement du plan). Notre implémentation (`handin/policy.py`)
  est encore un stub qui rate tous les scénarios — en cours chez Youcef.
- 102 % mesuré sur un seul scénario (L4 seed 3). Le chiffre solide est le
  **holdout** officiel : 50 graines par niveau jamais utilisées pour régler (5000–5049) :
  96 504 pts contre 63 989 pour le glouton (x1,51 global, x1,95 sur L4), 0 échec, 41,1 s au pire.
  Cohérent avec le banc d'entraînement (x1,53) : pas de signe de surapprentissage.
- Sur notre propre plan, le diagnostic de routage réel trouve encore ~167 pts
  librement gagnables (sans toucher au plan actuel) et 84 pts en concurrence
  avec un contact déjà servi pour les mêmes drones. Chiffre approximatif : le test par contact a
  un budget de temps (8 s par défaut, `DIAG_BUDGET_S`) ; sous forte charge machine, quelques
  contacts limites basculent sur l'estimation en ligne directe, ce qui fait varier ce total de
  quelques dizaines de points d'un lancement à l'autre.

## Vidéo de secours

Enregistrée sur le scénario de démo final (L4 seed 3), écran `view.html` +
`explication.md` ouverts côte à côte, sans narration improvisée. Répétition générale samedi
22h00 ; à réenregistrer si le plan change avant le gel (CP5, dimanche 10h) et le rendu
(dimanche 11h).
