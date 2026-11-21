# Slides : méthode et robustesse (CP3.5)

Source des slides en texte : un titre `##` par slide, le contenu à afficher, puis les notes orales. À coller
dans l'outil de présentation de l'équipe. Chaque chiffre vient d'une mesure rejouable (commande en bas de la
slide). Avant le pitch, relire le cadre « À revérifier » en fin de fichier : certains chiffres datent d'un
état précis de `main`.

Public visé : le jury. Durée cible : 5 slides pour le pitch, 3 de réserve pour les questions.

---

## Slide 1 : Le problème (pitch)

**Le glouton du kit laisse la moitié du possible sur la table.**

- Dix règles (R1 à R10) : collatéral, séparation 40 m, fenêtres de temps, engagement synchronisé.
- Score = points servis, moins 0,5 par Wh, moins 10 par effecteur utilisé. Un plan invalide vaut zéro.
- Au niveau L4 (100 drones, 70 contacts), le glouton atteint **34 % de la borne** (voir slide 4).

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

**Planificateur : 79 % de la borne. Glouton : 51 %.**

| Niveau | Borne moyenne | Notre plan | % de la borne | Glouton | % de la borne |
|---|---:|---:|---:|---:|---:|
| L1 | 108,7 | 101,7 | 93,5 % | 95,1 | 87,5 % |
| L2 | 265,9 | 250,9 | 94,4 % | 227,7 | 85,6 % |
| L3 | 530,3 | 490,4 | 92,5 % | 387,9 | 73,2 % |
| L4 | 1534,5 | 1081,3 | 70,5 % | 523,2 | 34,1 % |

Données : graines d'entraînement 0 à 49 par niveau, `main` au commit ec5c41e (200 runs, 0 invalide,
38,6 s au maximum, total 96 214,6 contre 61 695,6 pour le glouton, x1,56). Sur graines cachées
simulées (holdout 5000 à 5049, 200 runs) : **x1,51 global, x1,95 sur L4, 0 échec, 41,1 s au maximum**.

Notes : la borne est une borne supérieure, pas un score atteignable. Elle ignore la séparation R8, la
synchronisation R10 et le temps des éclaireurs. Un plan réel ne l'atteint donc jamais. Sur L1 à L3 on est
à plus de 92 % : il reste peu à gagner. Sur L4, le reste (30 %) vient probablement de R8 (le principal mur du glouton,
selon nos mesures de rejets), sans que ce soit prouvé pour notre plan. La borne ne fait jamais moins qu'un plan valide : 0 violation sur 200 plans réels.

Rejouer : `python3 tools/bound.py --bench bench.json` (sortie de `python3 tools/bench.py --json bench.json`).

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

- Perte de liaison : traitée à part (`linkloss/`), isolée du plan remis, pas de politique publiée au moment
  de la remise.
- L4 est à 70 % de la borne ; la borne est lâche (R8 ignorée), l'écart réel atteignable est inconnu.
- Les chiffres de la slide 4 portent sur des scénarios produits par le générateur du kit (le même que celui
  du jury), pas sur les scénarios cachés eux-mêmes.
- L'alarme de secours repose sur `SIGALRM`, qui n'existe pas sous Windows. La CI tourne sous Linux (Python 3.9).

---

## À revérifier avant le pitch

1. **Commit de référence.** Les chiffres de la slide 4 portent sur `main` ec5c41e (banc final du 21/11, graines
   d'entraînement). Les chiffres holdout (x1,51, x1,95) datent de `main` 55327de. Si `main` change, relancer :
   ```
   python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-49 --json bench.json
   python3 tools/bound.py --bench bench.json
   ```
   (plusieurs dizaines de minutes sur une machine inactive) et remplacer le tableau.
2. **Repli glouton.** La ligne « repli » de la slide 5 décrit la PR 7 : à garder seulement si elle est fusionnée.
3. **Budget.** Le budget est de 38 s dans `handin/params.py` : si l'équipe le change, mettre la slide à jour.
4. **Limite de durée du pitch.** Non connue de moi : les 5 slides de pitch visent environ 3 minutes.
