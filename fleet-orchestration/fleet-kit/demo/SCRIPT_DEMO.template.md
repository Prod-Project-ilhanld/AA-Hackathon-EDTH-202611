# Script de démo (2 minutes) — Fleet Orchestration

Pour le jury (anglais, 2 min 30, chiffres finaux) : voir `SCRIPT_JURY.md`. Ce fichier reste le script français
d'origine.

À adapter au scénario choisi avec l'équipe avant le pitch. Chiffres générés par
`python demo/gen_script_demo.py` sur {level} seed {seed} — ne pas les recopier à la main,
relancer le générateur à chaque nouveau plan.

## Accroche (20 s)

« Le kit fournit un glouton de référence. Sur ce scénario {level}, il sert {served_glouton} contacts
sur {servable_total} pour un score de {score_glouton} — et laisse {open_pts_glouton} points sur
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

« Résultat mesuré, pas estimé : glouton {score_glouton} → notre plan {score_ours} points,
**+{gain_pct} %**, plan valide sur les 10 règles, {served_ours} contacts servis contre
{served_glouton}. » (Afficher le tableau de score en haut de `explication.md`.)

## Clôture (10 s)

« Le même pipeline tourne sur n'importe quel plan et n'importe quel scénario en une commande — on
peut le rejouer en direct si le jury veut changer de scénario. »

## Limites à assumer si on nous les demande

- Perte de liaison : politique `handin/policy.py`, score de dimensionnement 1,00 / 1,00, 0 run en échec
  (`handin/LINKLOSS_FRONTIER.md`). Limite connue : L3-6, rétention 0,611.
- {gain_pct} % mesuré sur un seul scénario ({level} seed {seed}). Le chiffre solide est le jeu
  final (graines 9000 à 9049, jamais utilisées pour le réglage, 200 runs) : 99 580 pts contre 62 029 pour
  le glouton (x1,605 global, x2,22 sur L4), 0 plan invalide, 0 graine sous le glouton.
- Sur notre propre plan, le diagnostic de routage réel trouve encore ~{open_pts_ours} pts
  librement gagnables (sans toucher au plan actuel) et {contested_pts_ours} pts en concurrence
  avec un contact déjà servi pour les mêmes drones. Chiffre approximatif : le test par contact a
  un budget de temps (8 s par défaut, `DIAG_BUDGET_S`) ; sous forte charge machine, quelques
  contacts limites basculent sur l'estimation en ligne directe, ce qui fait varier ce total de
  quelques dizaines de points d'un lancement à l'autre.

## Vidéo de secours

Enregistrée sur le scénario de démo final ({level} seed {seed}), écran `view.html` +
`explication.md` ouverts côte à côte, sans narration improvisée. À réenregistrer si le plan
change avant le gel du code (dimanche 9h).
