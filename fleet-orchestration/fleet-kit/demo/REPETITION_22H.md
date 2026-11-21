# Répétition générale de 22 h (CP3.5)

Critère de réussite du point de contrôle : **passage complet sous la limite de durée du pitch, et chacun
sait répondre à « pourquoi cette cible ? »**. Je ne connais pas la limite de durée du pitch : à inscrire en
haut de la feuille avant de commencer. La répétition elle-même se fait à plusieurs, sur la machine de démo.

## Avant de commencer (10 min)

- [ ] Limite de durée du pitch connue : ______ min. Chronomètre visible.
- [ ] `main` à jour, `git log -1` noté : ______.
- [ ] Préparation faite (voir `VIDEO_SECOURS.md`) : `view.html` et `explication.md` s'ouvrent.
- [ ] Machine de démo : notifications coupées, texte du terminal agrandi, batterie branchée.
- [ ] Vidéo de secours lisible sur cette machine.
- [ ] Les chiffres des slides correspondent au dernier banc (voir « À revérifier » dans
      `SLIDES_METHODE_ROBUSTESSE.md`).

## Déroulé (à chronométrer)

| Étape | Qui (proposé) | Durée cible | Chronométré |
|---|---|---|---|
| Accroche et problème (slide 1) | Swann | 0:30 | |
| Méthode (slide 2) | Louis | 0:45 | |
| Démo en direct : `view.html`, calque Gagnés, `explication.md` | Swann | 1:00 | |
| Résultats et borne (slide 4) | Swann ou Ilhan | 0:30 | |
| Robustesse (slide 5) | Mahmoud | 0:30 | |
| Questions du jury | tous | selon la limite | |

Les durées cibles totalisent 3 min 15 hors questions : à ajuster à la limite réelle. Les rôles sont une
proposition, à confirmer ensemble. Faire un passage complet sans s'arrêter, puis un second après corrections.

## « Pourquoi cette cible ? » : une réponse par type de contact

Chacun doit pouvoir répondre en 20 secondes, avec un exemple de L4 seed 3 sous les yeux (`explication.md`,
section Contacts non servis).

| Question | Réponse courte | Exemple réel |
|---|---|---|
| Pourquoi ce contact est-il servi ? | Il rapporte beaucoup de points par effecteur et des drones proches peuvent l'atteindre dans sa fenêtre. | C35 : 78 pts, 2 lourds, engagé par H02 et H03 à 2,2 et 2,4 km. |
| Pourquoi ce contact à 85 points est-il ignoré ? | Une règle l'interdit. Aucun plan valide ne peut le servir. | C27 : à 140 m d'un civil, interdit par R7 (collatéral, 200 m). |
| Pourquoi celui-là, 84 points, aussi ? | Il est faisable seul, mais les drones qu'il lui faudrait servent un autre contact du plan. | C50 : 4 légers requis, déjà pris. Les légers sont rares à L4. |
| Pourquoi celui-là, 88 points ? | Aucun routage ne le sert dans sa fenêtre, même avec tous les drones : portée ou énergie. | C37 : routage réel testé, rien de valide. |
| Il reste des points à gagner ? | Oui, et le rapport les nomme. | C48 (49 pts) et C62 (23 pts) : routage réel réussi avec des drones au sol, à gagner. |
| Comment savez-vous que c'est bon ? | Chaque plan repasse par le validateur du kit, et on compare à une borne supérieure. | L4 seed 3 : 1076,7 pour une borne de 1319,6, soit 81,6 %. |
| Pourquoi pas un solveur optimal ? | À 100 drones, 70 contacts, 60 s : une recherche locale bat les solveurs appris, et on garde la main sur les règles. | Slide de réserve B. |

Attention : C35, C27, C50, C37, C48 et C62 viennent de L4 seed 3 avec le plan d'exemple. Si le plan de démo
change, relancer `swann_demo.py` et remplacer ces exemples.

## Questions pièges à préparer

| Question | Réponse honnête |
|---|---|
| « Ce chiffre est sur combien de scénarios ? » | Le +102 % est sur un seul scénario. Le chiffre solide est le banc : 50 graines par niveau, puis 50 graines cachées simulées (x1,51 global, x1,95 sur L4, 0 échec). |
| « Et si le programme plante chez nous ? » | Plan vide écrit d'abord, alarme à 52 s qui écrit le meilleur plan validé, contrôle final avec votre validateur, sortie code 0. Chaque panne est testée par injection. |
| « Pourquoi seulement 70 % de la borne à L4 ? » | La borne ignore la séparation R8 et le temps des éclaireurs. Elle est lâche : on ne sait pas ce qui est réellement atteignable. |
| « Vous avez surajusté sur vos scénarios ? » | Trois jeux de graines. Réglages sur l'entraînement (0 à 199), contrôle sur le holdout (5000 à 5049) : x1,53 contre x1,51, pas d'écart. |
| « Et la perte de liaison ? » | Traitée à part, isolée du plan remis. Pas de politique publiée par les organisateurs au moment de la remise. |

## Après la répétition (10 min)

- [ ] Durée réelle du passage complet : ______ (limite : ______).
- [ ] Questions où quelqu'un a hésité : ______ . Les réécrire dans ce fichier.
- [ ] Diapositives ou chiffres à corriger : ______ , avec le responsable de chacun.
- [ ] Vidéo de secours à refaire ? oui / non (oui si un chiffre ou le plan d'exemple a changé).
- [ ] Prochaine répétition prévue avant le gel du code (dimanche 10 h) ? ______
