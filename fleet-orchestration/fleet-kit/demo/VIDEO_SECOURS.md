# Vidéo de secours : plan de tournage

Une vidéo de 2 minutes de la démo, à lancer si l'affichage en direct tombe en panne (wifi, machine, visualiseur).
La vidéo elle-même n'est pas dans le dépôt : elle se tourne sur la machine de démo avec l'enregistreur d'écran
de macOS (`Cmd + Maj + 5`, « Enregistrer tout l'écran »). Ce fichier donne la préparation, le découpage et la
règle de mise à jour.

## Préparation (vérifiée : 37 s de calcul, produit les deux fichiers)

Depuis `fleet-kit/` :

```
python3 -m fleetkit generate L4 3 -o /tmp/s_l4.json
python3 demo/swann_demo.py /tmp/s_l4.json examples/plans/L4-seed3.plan.json -o /tmp/demo_l4
```

Sortie attendue : `Glouton 532.9 · notre plan 1076.7 (valide)`, puis `/tmp/demo_l4/view.html` et
`/tmp/demo_l4/explication.md`. Si ces deux chiffres changent, le plan ou le planificateur a changé : refaire
le script et le tournage.

Pour mettre à jour les chiffres du script de démo : `python3 demo/gen_script_demo.py /tmp/s_l4.json <plan>`.

Avant d'enregistrer : fermer les notifications, passer en mode ne pas déranger, agrandir le texte du terminal,
ouvrir `view.html` dans le navigateur et `explication.md` dans un second onglet.

## Découpage (2 min 00)

| Temps | Écran | Ce qu'on montre | Texte à dire |
|---|---|---|---|
| 0:00 à 0:15 | `explication.md`, tableau du haut | Glouton 532,9 contre notre plan 1076,7 | « Sur ce scénario L4 de 100 drones, le glouton du kit sert 18 contacts. Notre plan en sert 37. » |
| 0:15 à 0:45 | `view.html`, calque **Gagnés** | Les contacts verts du plan face au glouton | « En vert, ce que notre plan gagne en plus : 21 contacts. Le calque Perdus montre les deux que le glouton servait et pas nous. » |
| 0:45 à 1:15 | `explication.md`, **Contacts non servis** | C27 (R7), C50 (concurrence), C37 (aucun routage) | « Chaque contact non servi a une raison testée : une règle, une ressource ou la portée. » |
| 1:15 à 1:40 | terminal : `python3 tools/bound.py --levels L4 --seeds 3 --plan examples/plans/L4-seed3.plan.json` | La borne et le pourcentage | « La borne supérieure du scénario est 1320. Nous en atteignons 82 %. » |
| 1:40 à 2:00 | `explication.md`, section Ressources | Légers 48 sur 50 utilisés | « Les 50 effecteurs légers sont presque tous utilisés : c'est la ressource rare, et c'est ce qui borne le gain. » |

Sortie attendue de cette commande (0,1 s) : `L4-3 : plan valide, score 1076.7, borne 1319.6, soit 81.6 % de la borne`.

## Règles de tournage

- Pas de narration improvisée : lire le texte ci-dessus, deux prises au plus.
- Un seul scénario (L4 seed 3). Dire que c'est un exemple ; le chiffre solide est le banc, pas cette graine.
- Nommer le fichier `demo_secours_YYYYMMDD_HHMM.mp4` et en garder une copie sur deux machines.
- **À refaire** si le plan d'exemple, le planificateur ou les chiffres changent avant le gel du code
  (dimanche 10 h), ou si `view.html` change d'apparence.
- Tester la lecture de la vidéo sur la machine du pitch, son coupé, au moins une fois avant dimanche midi.
