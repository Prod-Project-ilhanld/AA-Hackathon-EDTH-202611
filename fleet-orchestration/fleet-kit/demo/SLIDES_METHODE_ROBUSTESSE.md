# Slides : méthode et robustesse (CP3.5)

Source des slides en texte : un titre `##` par slide, le contenu à afficher, puis les notes orales. À coller
dans l'outil de présentation de l'équipe. Chaque chiffre vient d'une mesure rejouable (commande en bas de la
slide). Avant le pitch, relire le cadre « À revérifier » en fin de fichier : certains chiffres datent d'un
état précis de `main`.

Public visé : le jury. Durée cible : 5 slides pour le pitch, 3 de réserve pour les questions.

**Pitch du jury (anglais, 2 min 30) : `SCRIPT_JURY.md`**, avec la diapositive de chiffres finaux. Les chiffres de la
slide 4 ci-dessous ont été remplacés par ceux du jeu final ; les pourcentages de la borne (`main` ec5c41e) ne sont plus
à jour et ne sont plus cités.

---

## Slide 1 : Le problème (pitch)

**Le glouton du kit laisse la moitié du possible sur la table.**

- Dix règles (R1 à R10) : collatéral, séparation 40 m, fenêtres de temps, engagement synchronisé.
- Score = points servis, moins 0,5 par Wh, moins 10 par effecteur utilisé. Un plan invalide vaut zéro.
- Au niveau L4 (100 drones, 70 contacts), le glouton atteint **34 % de la borne** (banc d'entraînement, graines 0 à 49).

Notes : le jury regarde la somme des scores sur des scénarios cachés. Un seul plan invalide ou en retard
vaut zéro, donc la prudence compte autant que le gain.

---

## Slide 2 : La méthode (pitch)

**Construire, mesurer, réordonner, relancer, vérifier.**

1. **Construire** : pour chaque contact hostile, on cherche l'éclaireur puis les effecteurs qui le servent,
   avec 15 éclaireurs testés et toutes leurs options (délai d'arrivée des effecteurs 0, 20, 90 s).
2. **Contrôler vite** : chaque essai ne revalide que les routes touchées (environ 3 fois plus d'essais par
   seconde qu'une validation complète).
3. **Réordonner** : l'ordre des contacts est la décision clé. Clé de tri : points par effecteur requis,
   avec un petit bruit, puis relances autour du meilleur ordre trouvé.
4. **Paralléliser** : jusqu'à 8 processus, budget de 38 s depuis le démarrage du programme.
5. **Vérifier** : le plan final repasse par le validateur du kit. Invalide : on ne le remet jamais.

Notes : un effecteur ne sert qu'une fois (son vol finit par l'engagement), donc les effecteurs légers sont
la ressource rare à L4 : 49 à 86 en demande pour 50 disponibles. D'où le tri par points par effecteur.

---

## Slide 3 : Pourquoi cette cible ? (pitch)

**Chaque contact non servi a une raison vérifiable, pas une estimation.**

Exemple réel, L4 seed 3, rapport `explication.md` :
- **C35** servi (78 pts, 2 effecteurs lourds, fenêtre 171 à 503 s) : engagé par H02 et H03, à 2,2 et 2,4 km,
  pour 8,3 et 6,8 Wh. Soit 39 pts par effecteur.
- **C27** écarté (85 pts) : à 140 m d'un civil, interdit par R7. Aucun plan valide ne le sert.
- **C50** écarté (84 pts, 4 légers) : routable seul, mais les drones nécessaires sont déjà pris par un autre
  contact du plan. Concurrence de ressources.
- **C37** écarté (88 pts) : aucun routage trouvé même avec tous les drones, essai de routage réel.

Notes : c'est la question du jury (« pourquoi cette cible ? »). La réponse tient en trois mots : règle
(R7), ressource (légers), portée (fenêtre ou énergie). Le rapport donne la raison de chacun des 27 contacts
non servis sur ce scénario.

---

## Slide 4 : Où on en est, mesuré (pitch)

**Sur des graines jamais vues : x1,6 au total, x2,2 sur L4. Jamais sous le glouton.**

| Niveau | Notre plan contre le glouton du kit |
|---|---:|
| L1 | x1,088 |
| L2 | x1,073 |
| L3 | x1,265 |
| L4 | **x2,22** |
| Total | **x1,605** (99 580 contre 62 029) |

Données : jeu final, graines 9000 à 9049, jamais utilisées pour le réglage, 200 runs, Python 3.9.6, 2 cœurs par run
(prudent). 0 plan invalide, 0 graine sous le glouton sur 200 : le planificateur rend le meilleur de son plan et de
celui du glouton, il ne peut donc pas faire moins par construction. Les 8 scénarios publics : 8/8 valides, 4252,9
contre 2748,6, 39,5 s au maximum sur 60 s.

Notes : le gain vient de L4, où drones et effecteurs sont disputés (les 50 effecteurs légers sont tous utilisés sur
L4 graine 3). Sur L1 et L2, le glouton prend déjà l'essentiel du possible.

---

## Slide 5 : Robustesse (pitch)

**Un zéro coûte plus cher que tout gain. Le programme ne peut pas rendre un plan invalide.**

- **Plan vide écrit en premier**, avant même de lire le scénario.
- **Écritures atomiques** : le fichier de plan est toujours entier.
- **Budget mesuré depuis le démarrage du processus** (38 s), pas depuis la fin des imports.
- **Alarme de secours à 52 s** : écrit le meilleur plan validé et sort.
- **Contrôle final** avec le validateur du kit ; invalide ou négatif : repli, jamais de plan faux.
- **Toujours code de sortie 0**, même en cas d'exception.
- **Reproductible** : `FLEET_ITERS` fixe le nombre d'itérations, mêmes plans à l'octet près.
- **Intégration continue** : Python 3.9, tests des règles, banc de style jury, interdits vérifiés.

Notes : chaque garde-fou a un test qui injecte la panne (exception dans `solve()`, blocage après le meilleur
plan, alarme trop proche). Un test non lancé n'est pas une garde.

---

## Réserve A : Ce qu'on a essayé et abandonné

Un chiffre par essai, mesuré sur graines d'entraînement :

| Idée | Résultat | Décision |
|---|---|---|
| Reprise de préfixe entre constructions | mesurée, sans intérêt | abandonnée |
| Passe de polissage finale | -0,9 % sur L4 | abandonnée |
| Options élargies pour les éclaireurs | -6 à -12 % sur L4 | abandonnée |
| Prix fictifs légers et lourds | +0,4 %, -0,73 %, -0,48 % : du bruit | gardés éteints |
| Saut des hostiles bloqués par R7 | **+1,27 % sur L4, 0 graine moins bonne** | **activé par défaut** |

Notes : on ne garde un changement que s'il gagne en moyenne, avec au plus 40 % de graines moins bonnes et
zéro plan invalide. Le bruit de rejeu est de 0,1 à 0,5 %.

---

## Réserve B : Pourquoi pas de solveur appris ?

Solveurs appris (RL, POMO) : torch et GPU requis, ni synchronisation ni séparation, moins bons qu'une
recherche locale en 60 s. Bonus de vérification : n'a pas d'effet sur le classement. Frappe à 2 points de
passage sous 30 m : gain d'au plus 0,5 point par effecteur, risque de faille. Écartés volontairement.

---

## Réserve C : Limites assumées

- Perte de liaison : politique `handin/policy.py`, score de dimensionnement 1,00 / 1,00, 0 run en échec
  (`handin/LINKLOSS_FRONTIER.md`). Limite connue : L3-6, rétention 0,611 (deux drones abandonnent au-dessus de la base).
- L4 : x2,22 sur graines jamais vues ; la borne supérieure est lâche (R8 ignorée), l'écart réel atteignable est inconnu.
- Les chiffres de la slide 4 portent sur des scénarios produits par le générateur du kit (le même que celui
  du jury), pas sur les scénarios cachés eux-mêmes.
- L'alarme de secours repose sur `SIGALRM`, qui n'existe pas sous Windows. La CI tourne sous Linux (Python 3.9).

---

## À revérifier avant le pitch

1. **Commit de référence.** Les chiffres de la slide 4 portent sur le tag `handin-final` (c33b1ef), jeu final
   9000 à 9049. Le code est gelé : ne plus les changer. Pour rejouer la borne sur l'entraînement :
   ```
   python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-49 --json bench.json
   python3 tools/bound.py --bench bench.json
   ```
   (plusieurs dizaines de minutes sur une machine inactive).
2. **Repli glouton.** La ligne « repli » de la slide 5 décrit la PR 7 : à garder seulement si elle est fusionnée.
3. **Budget.** Le budget est de 38 s dans `handin/params.py` : si l'équipe le change, mettre la slide à jour.
4. **Limite de durée du pitch.** 2 min 30 (fenêtre de 2 à 3 minutes), en anglais : voir `SCRIPT_JURY.md`.
