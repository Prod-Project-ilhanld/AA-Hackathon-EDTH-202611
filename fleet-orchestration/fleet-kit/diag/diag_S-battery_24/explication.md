# Explication du plan · scénario S-battery seed 24

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 201.7 | 428.6 |
| Points servis | 521.0 | 1010.0 |
| Énergie (Wh) | 278.7 | 562.9 |
| Drones d'action consommés | 18 | 30 |
| Contacts servis | 8 | 18 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+113 %** par rapport au glouton (201.7 → 428.6 pts).

Gagnés par rapport au glouton : C01, C05, C17, C34, C42, C48, C52, C54, C63, C70 · perdus : aucun.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 5 | 30 |
| effector (light) | 50 | 25 | 25 |
| scout | 15 | 11 | 4 |

Drones au sol : H01, H02, H03, H04, H05, H06, H07, H08, H09, H11, H13, H14, H15, H16, H17, H19, H20, H21, H22, H23, H24, H25, H26, H27, H28, H29, H30, H31, H32, H34, L01, L02, L05, L07, L08, L10, L11, L15, L16, L20, L21, L22, L23, L27, L28, L33, L34, L37, L38, L41, L42, L43, L44, L45, L46, S01, S09, S12, S14.

## Affectations, drone par drone

### H10 · effector (heavy)

Distance 5.48 km · énergie 12.7 Wh sur 26.0 Wh utilisables · coût 6.4 pts.

- t = 350 s · engage **C34** (hostile, 80 pts, fenêtre 68–362 s)

### H12 · effector (heavy)

Distance 5.49 km · énergie 17.4 Wh sur 43.5 Wh utilisables · coût 8.7 pts.

- t = 343 s · engage **C34** (hostile, 80 pts, fenêtre 68–362 s)

### H18 · effector (heavy)

Distance 5.56 km · énergie 19.0 Wh sur 40.4 Wh utilisables · coût 9.5 pts.

- t = 356 s · engage **C01** (hostile, 88 pts, fenêtre 133–370 s)

### H33 · effector (heavy)

Distance 5.56 km · énergie 18.2 Wh sur 33.3 Wh utilisables · coût 9.1 pts.

- t = 357 s · engage **C01** (hostile, 88 pts, fenêtre 133–370 s)

### H35 · effector (heavy)

Distance 5.89 km · énergie 19.2 Wh sur 37.9 Wh utilisables · coût 9.6 pts.

- t = 382 s · engage **C48** (hostile, 68 pts, fenêtre 350–646 s)

### L03 · effector (light)

Distance 6.04 km · énergie 9.5 Wh sur 22.4 Wh utilisables · coût 4.8 pts.

- t = 406 s · engage **C45** (hostile, 90 pts, fenêtre 86–427 s)

### L04 · effector (light)

Distance 5.25 km · énergie 8.3 Wh sur 23.7 Wh utilisables · coût 4.1 pts.

- t = 441 s · engage **C13** (hostile, 60 pts, fenêtre 390–597 s)

### L06 · effector (light)

Distance 5.34 km · énergie 9.8 Wh sur 19.0 Wh utilisables · coût 4.9 pts.

- t = 514 s · engage **C37** (hostile, 70 pts, fenêtre 477–730 s)

### L09 · effector (light)

Distance 3.75 km · énergie 8.7 Wh sur 22.2 Wh utilisables · coût 4.3 pts.

- t = 576 s · engage **C47** (hostile, 78 pts, fenêtre 444–774 s)

### L12 · effector (light)

Distance 3.53 km · énergie 5.9 Wh sur 27.2 Wh utilisables · coût 3.0 pts.

- t = 645 s · engage **C23** (hostile, 44 pts, fenêtre 413–725 s)

### L13 · effector (light)

Distance 3.43 km · énergie 6.4 Wh sur 23.8 Wh utilisables · coût 3.2 pts.

- t = 253 s · engage **C05** (hostile, 65 pts, fenêtre 126–339 s)

### L14 · effector (light)

Distance 6.04 km · énergie 9.3 Wh sur 34.5 Wh utilisables · coût 4.6 pts.

- t = 408 s · engage **C42** (hostile, 52 pts, fenêtre 359–658 s)

### L17 · effector (light)

Distance 5.34 km · énergie 9.0 Wh sur 32.6 Wh utilisables · coût 4.5 pts.

- t = 520 s · engage **C37** (hostile, 70 pts, fenêtre 477–730 s)

### L18 · effector (light)

Distance 3.54 km · énergie 5.7 Wh sur 23.6 Wh utilisables · coût 2.8 pts.

- t = 650 s · engage **C23** (hostile, 44 pts, fenêtre 413–725 s)

### L19 · effector (light)

Distance 5.34 km · énergie 8.6 Wh sur 32.1 Wh utilisables · coût 4.3 pts.

- t = 384 s · engage **C43** (hostile, 93 pts, fenêtre 341–642 s)

### L24 · effector (light)

Distance 3.72 km · énergie 5.8 Wh sur 27.4 Wh utilisables · coût 2.9 pts.

- t = 581 s · engage **C47** (hostile, 78 pts, fenêtre 444–774 s)

### L25 · effector (light)

Distance 6.05 km · énergie 10.8 Wh sur 24.5 Wh utilisables · coût 5.4 pts.

- t = 411 s · engage **C45** (hostile, 90 pts, fenêtre 86–427 s)

### L26 · effector (light)

Distance 3.41 km · énergie 5.7 Wh sur 28.2 Wh utilisables · coût 2.9 pts.

- t = 248 s · engage **C05** (hostile, 65 pts, fenêtre 126–339 s)

### L29 · effector (light)

Distance 3.73 km · énergie 8.0 Wh sur 29.4 Wh utilisables · coût 4.0 pts.

- t = 571 s · engage **C47** (hostile, 78 pts, fenêtre 444–774 s)

### L30 · effector (light)

Distance 3.52 km · énergie 4.9 Wh sur 35.0 Wh utilisables · coût 2.5 pts.

- t = 538 s · engage **C41** (hostile, 43 pts, fenêtre 447–671 s)

### L31 · effector (light)

Distance 5.91 km · énergie 9.5 Wh sur 19.4 Wh utilisables · coût 4.8 pts.

- t = 387 s · engage **C48** (hostile, 68 pts, fenêtre 350–646 s)

### L32 · effector (light)

Distance 3.54 km · énergie 6.5 Wh sur 20.3 Wh utilisables · coût 3.2 pts.

- t = 543 s · engage **C41** (hostile, 43 pts, fenêtre 447–671 s)

### L35 · effector (light)

Distance 5.25 km · énergie 10.3 Wh sur 32.6 Wh utilisables · coût 5.1 pts.

- t = 440 s · engage **C13** (hostile, 60 pts, fenêtre 390–597 s)

### L36 · effector (light)

Distance 3.39 km · énergie 4.9 Wh sur 33.1 Wh utilisables · coût 2.5 pts.

- t = 507 s · engage **C29** (hostile, 43 pts, fenêtre 450–790 s)

### L39 · effector (light)

Distance 3.39 km · énergie 5.8 Wh sur 26.2 Wh utilisables · coût 2.9 pts.

- t = 512 s · engage **C29** (hostile, 43 pts, fenêtre 450–790 s)

### L40 · effector (light)

Distance 3.45 km · énergie 6.3 Wh sur 29.0 Wh utilisables · coût 3.2 pts.

- t = 257 s · engage **C05** (hostile, 65 pts, fenêtre 126–339 s)

### L47 · effector (light)

Distance 5.35 km · énergie 8.8 Wh sur 27.2 Wh utilisables · coût 4.4 pts.

- t = 519 s · engage **C37** (hostile, 70 pts, fenêtre 477–730 s)

### L48 · effector (light)

Distance 3.42 km · énergie 6.4 Wh sur 25.4 Wh utilisables · coût 3.2 pts.

- t = 247 s · engage **C05** (hostile, 65 pts, fenêtre 126–339 s)

### L49 · effector (light)

Distance 5.24 km · énergie 9.0 Wh sur 25.5 Wh utilisables · coût 4.5 pts.

- t = 430 s · engage **C13** (hostile, 60 pts, fenêtre 390–597 s)

### L50 · effector (light)

Distance 4.33 km · énergie 6.8 Wh sur 28.0 Wh utilisables · coût 3.4 pts.

- t = 319 s · engage **C17** (hostile, 48 pts, fenêtre 171–388 s)

### S02 · scout

Distance 7.72 km · énergie 21.1 Wh sur 21.5 Wh utilisables · coût 10.5 pts.

- t = 413 s · observe **C23** (hostile, 44 pts, fenêtre 413–725 s)
- t = 472 s · observe **C29** (hostile, 43 pts, fenêtre 450–790 s)
- t = 506 s · observe **C41** (hostile, 43 pts, fenêtre 447–671 s)

### S03 · scout

Distance 9.69 km · énergie 28.7 Wh sur 28.9 Wh utilisables · coût 14.4 pts.

- t = 271 s · observe **C63** (unknown, 29 pts, fenêtre 85–423 s)

### S04 · scout

Distance 8.55 km · énergie 24.9 Wh sur 26.7 Wh utilisables · coût 12.5 pts.

- t = 216 s · observe **C05** (hostile, 65 pts, fenêtre 126–339 s)
- t = 288 s · observe **C17** (hostile, 48 pts, fenêtre 171–388 s)
- t = 395 s · observe **C54** (unknown, 14 pts, fenêtre 224–432 s)

### S05 · scout

Distance 11.97 km · énergie 25.7 Wh sur 26.3 Wh utilisables · coût 12.8 pts.

- t = 350 s · observe **C48** (hostile, 68 pts, fenêtre 350–646 s)
- t = 376 s · observe **C42** (hostile, 52 pts, fenêtre 359–658 s)

### S06 · scout

Distance 10.39 km · énergie 28.3 Wh sur 28.6 Wh utilisables · coût 14.2 pts.

- t = 398 s · observe **C13** (hostile, 60 pts, fenêtre 390–597 s)

### S07 · scout

Distance 10.84 km · énergie 28.0 Wh sur 28.1 Wh utilisables · coût 14.0 pts.

- t = 306 s · observe **C34** (hostile, 80 pts, fenêtre 68–362 s)

### S08 · scout

Distance 7.19 km · énergie 23.0 Wh sur 23.2 Wh utilisables · coût 11.5 pts.

- t = 444 s · observe **C47** (hostile, 78 pts, fenêtre 444–774 s)

### S10 · scout

Distance 10.51 km · énergie 26.6 Wh sur 26.8 Wh utilisables · coût 13.3 pts.

- t = 477 s · observe **C37** (hostile, 70 pts, fenêtre 477–730 s)

### S11 · scout

Distance 8.12 km · énergie 22.4 Wh sur 25.9 Wh utilisables · coût 11.2 pts.

- t = 485 s · observe **C52** (unknown, 21 pts, fenêtre 480–707 s)

### S13 · scout

Distance 11.03 km · énergie 24.5 Wh sur 25.0 Wh utilisables · coût 12.3 pts.

- t = 319 s · observe **C01** (hostile, 88 pts, fenêtre 133–370 s)
- t = 352 s · observe **C43** (hostile, 93 pts, fenêtre 341–642 s)

### S15 · scout

Distance 12.00 km · énergie 32.4 Wh sur 32.7 Wh utilisables · coût 16.2 pts.

- t = 374 s · observe **C45** (hostile, 90 pts, fenêtre 86–427 s)
- t = 494 s · observe **C70** (unknown, 24 pts, fenêtre 392–676 s)

## Contacts non servis

- **C38** · hostile, 99 pts, besoin : 1 light, fenêtre 200–461 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C39** · hostile, 99 pts, besoin : 1 light, 1 heavy, fenêtre 191–527 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C35** · hostile, 97 pts, besoin : 3 light, fenêtre 294–612 s · interdit par R7 (à 185 m de C83, civilian)
- **C08** · hostile, 96 pts, besoin : 1 light, fenêtre 140–352 s · interdit par R7 (à 127 m de C77, friendly)
- **C32** · hostile, 95 pts, besoin : 1 light, 2 heavy, fenêtre 419–759 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C33** · hostile, 95 pts, besoin : 1 light, 1 heavy, fenêtre 273–583 s · interdit par R7 (à 160 m de C73, friendly)
- **C03** · hostile, 93 pts, besoin : 1 heavy, fenêtre 17–272 s · interdit par R7 (à 113 m de C73, friendly)
- **C25** · hostile, 91 pts, besoin : 2 light, fenêtre 1–281 s · interdit par R7 (à 112 m de C83, civilian)
- **C15** · hostile, 89 pts, besoin : 2 light, 1 heavy, fenêtre 289–533 s · interdit par R7 (à 133 m de C73, friendly)
- **C46** · hostile, 85 pts, besoin : 1 light, fenêtre 121–390 s · interdit par R7 (à 115 m de C78, friendly)
- **C26** · hostile, 84 pts, besoin : 1 light, fenêtre 268–597 s · interdit par R7 (à 136 m de C77, friendly)
- **C19** · hostile, 82 pts, besoin : 1 light, fenêtre 52–329 s · interdit par R7 (à 155 m de C80, friendly)
- **C20** · hostile, 81 pts, besoin : 4 light, fenêtre 38–258 s · interdit par R7 (à 196 m de C77, friendly)
- **C31** · hostile, 81 pts, besoin : 1 light, 1 heavy, fenêtre 281–480 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C12** · hostile, 78 pts, besoin : 1 light, 2 heavy, fenêtre 422–683 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C24** · hostile, 78 pts, besoin : 1 light, 2 heavy, fenêtre 126–476 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C28** · hostile, 78 pts, besoin : 3 light, fenêtre 142–346 s · interdit par R7 (à 96 m de C78, friendly)
- **C40** · hostile, 78 pts, besoin : 1 light, fenêtre 457–708 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C02** · hostile, 75 pts, besoin : 1 light, fenêtre 188–520 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C10** · hostile, 74 pts, besoin : 1 light, fenêtre 169–494 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C21** · hostile, 72 pts, besoin : 2 light, 1 heavy, fenêtre 265–479 s · interdit par R7 (à 149 m de C82, friendly)
- **C06** · hostile, 71 pts, besoin : 1 light, 1 heavy, fenêtre 161–484 s · interdit par R7 (à 119 m de C90, civilian)
- **C50** · hostile, 71 pts, besoin : 1 light, fenêtre 164–475 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C30** · hostile, 69 pts, besoin : 4 light, fenêtre 462–733 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C09** · hostile, 68 pts, besoin : 1 light, fenêtre 416–719 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C44** · hostile, 68 pts, besoin : 3 light, fenêtre 407–723 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C07** · hostile, 67 pts, besoin : 2 light, fenêtre 353–694 s · interdit par R7 (à 171 m de C80, friendly)
- **C27** · hostile, 65 pts, besoin : 1 light, 2 heavy, fenêtre 74–389 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C22** · hostile, 58 pts, besoin : 1 light, 1 heavy, fenêtre 44–262 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C18** · hostile, 48 pts, besoin : 1 light, 1 heavy, fenêtre 342–590 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C04** · hostile, 47 pts, besoin : 2 light, fenêtre 419–638 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C49** · hostile, 47 pts, besoin : 2 heavy, fenêtre 368–639 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C36** · hostile, 44 pts, besoin : 2 light, fenêtre 476–736 s · interdit par R7 (à 176 m de C85, civilian)
- **C16** · hostile, 43 pts, besoin : 2 heavy, fenêtre 348–535 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C14** · hostile, 41 pts, besoin : 1 light, fenêtre 471–765 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C11** · hostile, 40 pts, besoin : 1 light, 2 heavy, fenêtre 88–327 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C60** · unknown, 30 pts, besoin : observation, fenêtre 389–705 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C62** · unknown, 30 pts, besoin : observation, fenêtre 308–666 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C69** · unknown, 30 pts, besoin : observation, fenêtre 18–203 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C67** · unknown, 29 pts, besoin : observation, fenêtre 197–467 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C65** · unknown, 28 pts, besoin : observation, fenêtre 364–654 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C51** · unknown, 22 pts, besoin : observation, fenêtre 215–567 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C53** · unknown, 19 pts, besoin : observation, fenêtre 14–268 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C57** · unknown, 19 pts, besoin : observation, fenêtre 292–517 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C55** · unknown, 17 pts, besoin : observation, fenêtre 69–373 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C58** · unknown, 17 pts, besoin : observation, fenêtre 122–310 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C59** · unknown, 16 pts, besoin : observation, fenêtre 114–353 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C61** · unknown, 16 pts, besoin : observation, fenêtre 248–567 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C64** · unknown, 16 pts, besoin : observation, fenêtre 456–810 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C68** · unknown, 13 pts, besoin : observation, fenêtre 120–366 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C56** · unknown, 11 pts, besoin : observation, fenêtre 432–742 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C66** · unknown, 10 pts, besoin : observation, fenêtre 431–647 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **257 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **0 pts** (gagnable seulement en sacrifiant un autre contact).
