# Vue opérateur (opsview)

Le visualiseur du kit, avec des ajouts d'équipe pour une lecture plus technique : symbologie, repérage, ressources,
explication par contact, caméra de suivi. **Le dossier `fleetkit/` n'est pas modifié** : `OpsViewer` hérite de
`fleetkit.viewer.Viewer` et rend la page avec les fichiers de ce dossier. La vue de base reste intacte et sert de secours.

## Usage (depuis `fleet-kit/`)

```
python3 demo/opsview/opsview.py scenario.json plan.json -o out/view_ops.html
python3 demo/opsview/opsview.py scenario.json plan.json -o out/view_ops.html --diagnose   # raisons réelles, ~50 s sur L4
```

En Python : `OpsViewer(scenario, plan, title=..., reasons=reasons_from_diagnosis(diag)).save("view_ops.html")`.
Les calques de `Viewer.layer(...)` marchent à l'identique.

## Ce que la page ajoute

| Fonction | Détail |
|---|---|
| Bandeau « EXERCISE · SIMULATED DATA » | haut et bas de page, comme les outils réels |
| Horloge `H+hh:mm:ss` | temps de mission relatif : la convention réelle quand il n'y a pas d'heure absolue |
| Thèmes clair, sombre, nuit | touche T |
| Symboles | losange rouge hostile, rectangle bleu ami, carré vert civil, trèfle jaune inconnu (cadres inspirés d'APP-6) |
| Grille locale | cellules de 1 km, lettres en haut, chiffres à droite, lecture `GRID A2 · x · y` sous le curseur |
| Drones | icônes agrandies avec contour, compteur « ×N on pad » au départ |
| Jauges de flotte | éclaireurs, légers, lourds : utilisés sur disponibles |
| Score en direct | points, énergie et effecteurs consommés jusqu'à l'instant courant ; finit sur le score officiel du kit |
| Onglet **Why** | une fiche par contact : observation, confirmation, engagement, règles R4, R7, R9, raison s'il n'est pas servi |
| Onglet **Feed** | fil d'événements cliquable (observations, engagements, points gagnés) |
| HUD d'un drone | rôle, statut, altitude, vitesse, batterie, tâches ; bouton **Follow** (touche G) |
| **Replay engagement** | zoom sur le contact et lecture à 1× depuis 18 s avant le premier engagement |
| Décompte des drones | utiles (strike ou spotter), gaspillés, inactifs ; clic = surbrillance sur la carte ; pastille verte, rouge ou creuse sur chaque drone |
| Onglet **Fleet** | rôle de chaque drone, part de points (points d'un contact servi répartis à parts égales entre les drones qui l'ont servi) |
| Bandeau du bas | **Activity** : drones en transit, en observation, en retour, engagés, à l'instant courant ; **Altitude** : un drone ou un contact isolé, bande 30 à 150 m |
| Touches | N et P : événement suivant ou précédent ; S : export PNG de la carte |

## Honnêteté des données

- Tout ce qui est affiché vient du plan et du scénario : fleet, observations, engagements, marge R4, distance R7.
- **Raison d'un contact non servi** : R7 est calculée exactement. Les autres causes (concurrence, portée, à gagner) ne
  sont affichées que si `--diagnose` (ou `reasons=`) les fournit. Sinon la fiche dit « cause non calculée ici ».
- **Score en direct** : l'énergie échantillonnée diffère de quelques Wh du total exact du kit, elle est donc mise à
  l'échelle pour que la valeur finale soit exactement le score officiel (1076,7 sur L4 graine 3). Le coût d'un
  effecteur est compté à son engagement.
- **Symbologie** : cadres inspirés d'APP-6, pas une conformité APP-6 (pas d'insignes, pas de marquages de classification).
- **Grille et temps** : les positions du kit sont des mètres locaux et le temps est relatif. La grille est donc locale
  (pas du MGRS) et l'horloge est `H+` (pas de l'heure Zulu), pour ne pas afficher de fausses coordonnées.
- Données simulées : l'écart avec un usage opérationnel (incertitude capteurs, communications, cadre légal) n'est pas couvert.

## Fichiers

`opsview.py` (modèle et rendu), `app.js`, `style.css`, `template.html` : copies de la vue de base étendues.
Tests : `tests/test_opsview.py`. Aucune dépendance en dehors de la bibliothèque standard ; la page n'appelle aucun réseau.
