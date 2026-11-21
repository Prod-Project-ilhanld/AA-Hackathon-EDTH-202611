# Explication du plan · scénario S-half-scouts seed 0

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 307.0 | 685.7 |
| Points servis | 687.0 | 1391.0 |
| Énergie (Wh) | 400.0 | 710.7 |
| Drones d'action consommés | 18 | 35 |
| Contacts servis | 9 | 23 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+123 %** par rapport au glouton (307.0 → 685.7 pts).

Gagnés par rapport au glouton : C05, C08, C12, C16, C17, C20, C30, C36, C40, C41, C47, C52, C54, C61, C64, C67 · perdus : C26, C66.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 14 | 21 |
| effector (light) | 50 | 21 | 29 |
| scout | 7 | 7 | 0 |

Drones au sol : H03, H04, H05, H06, H07, H08, H11, H12, H13, H14, H20, H21, H22, H23, H24, H27, H28, H31, H33, H34, H35, L01, L03, L05, L07, L08, L11, L12, L13, L15, L16, L18, L19, L21, L25, L26, L30, L34, L36, L37, L38, L39, L40, L41, L42, L43, L44, L45, L47, L50.

## Affectations, drone par drone

### H01 · effector (heavy)

Distance 6.00 km · énergie 20.0 Wh sur 53.0 Wh utilisables · coût 10.0 pts.

- t = 549 s · engage **C27** (hostile, 72 pts, fenêtre 471–766 s)

### H02 · effector (heavy)

Distance 6.26 km · énergie 15.3 Wh sur 55.5 Wh utilisables · coût 7.7 pts.

- t = 458 s · engage **C17** (hostile, 63 pts, fenêtre 389–666 s)

### H09 · effector (heavy)

Distance 6.13 km · énergie 19.9 Wh sur 61.5 Wh utilisables · coût 9.9 pts.

- t = 549 s · engage **C38** (hostile, 92 pts, fenêtre 374–605 s)

### H10 · effector (heavy)

Distance 5.42 km · énergie 17.0 Wh sur 48.6 Wh utilisables · coût 8.5 pts.

- t = 553 s · engage **C12** (hostile, 65 pts, fenêtre 407–656 s)

### H15 · effector (heavy)

Distance 6.14 km · énergie 22.6 Wh sur 69.0 Wh utilisables · coût 11.3 pts.

- t = 547 s · engage **C38** (hostile, 92 pts, fenêtre 374–605 s)

### H16 · effector (heavy)

Distance 5.42 km · énergie 17.2 Wh sur 72.4 Wh utilisables · coût 8.6 pts.

- t = 334 s · engage **C43** (hostile, 95 pts, fenêtre 136–490 s)

### H17 · effector (heavy)

Distance 6.39 km · énergie 15.3 Wh sur 52.0 Wh utilisables · coût 7.7 pts.

- t = 425 s · engage **C16** (hostile, 61 pts, fenêtre 365–604 s)

### H18 · effector (heavy)

Distance 6.71 km · énergie 23.5 Wh sur 57.6 Wh utilisables · coût 11.7 pts.

- t = 403 s · engage **C40** (hostile, 79 pts, fenêtre 234–576 s)

### H19 · effector (heavy)

Distance 6.54 km · énergie 22.2 Wh sur 52.4 Wh utilisables · coût 11.1 pts.

- t = 417 s · engage **C36** (hostile, 47 pts, fenêtre 368–722 s)

### H25 · effector (heavy)

Distance 5.13 km · énergie 13.5 Wh sur 62.8 Wh utilisables · coût 6.8 pts.

- t = 510 s · engage **C23** (hostile, 79 pts, fenêtre 478–758 s)

### H26 · effector (heavy)

Distance 5.41 km · énergie 15.1 Wh sur 54.8 Wh utilisables · coût 7.6 pts.

- t = 328 s · engage **C43** (hostile, 95 pts, fenêtre 136–490 s)

### H29 · effector (heavy)

Distance 5.50 km · énergie 15.5 Wh sur 53.6 Wh utilisables · coût 7.7 pts.

- t = 284 s · engage **C47** (hostile, 97 pts, fenêtre 13–295 s)

### H30 · effector (heavy)

Distance 6.45 km · énergie 18.6 Wh sur 47.6 Wh utilisables · coût 9.3 pts.

- t = 482 s · engage **C05** (hostile, 54 pts, fenêtre 314–563 s)

### H32 · effector (heavy)

Distance 6.92 km · énergie 20.5 Wh sur 64.4 Wh utilisables · coût 10.3 pts.

- t = 422 s · engage **C30** (hostile, 60 pts, fenêtre 130–471 s)

### L02 · effector (light)

Distance 6.72 km · énergie 9.7 Wh sur 38.1 Wh utilisables · coût 4.8 pts.

- t = 378 s · engage **C20** (hostile, 86 pts, fenêtre 198–440 s)

### L04 · effector (light)

Distance 6.19 km · énergie 11.3 Wh sur 38.7 Wh utilisables · coût 5.7 pts.

- t = 552 s · engage **C38** (hostile, 92 pts, fenêtre 374–605 s)

### L06 · effector (light)

Distance 5.25 km · énergie 8.9 Wh sur 39.4 Wh utilisables · coût 4.4 pts.

- t = 569 s · engage **C12** (hostile, 65 pts, fenêtre 407–656 s)

### L09 · effector (light)

Distance 5.89 km · énergie 10.3 Wh sur 41.0 Wh utilisables · coût 5.1 pts.

- t = 592 s · engage **C08** (hostile, 56 pts, fenêtre 352–693 s)

### L10 · effector (light)

Distance 5.41 km · énergie 10.6 Wh sur 30.3 Wh utilisables · coût 5.3 pts.

- t = 343 s · engage **C43** (hostile, 95 pts, fenêtre 136–490 s)

### L14 · effector (light)

Distance 6.73 km · énergie 11.4 Wh sur 39.6 Wh utilisables · coût 5.7 pts.

- t = 383 s · engage **C20** (hostile, 86 pts, fenêtre 198–440 s)

### L17 · effector (light)

Distance 5.25 km · énergie 8.5 Wh sur 39.7 Wh utilisables · coût 4.2 pts.

- t = 568 s · engage **C12** (hostile, 65 pts, fenêtre 407–656 s)

### L20 · effector (light)

Distance 5.32 km · énergie 10.4 Wh sur 40.4 Wh utilisables · coût 5.2 pts.

- t = 325 s · engage **C48** (hostile, 83 pts, fenêtre 138–496 s)

### L22 · effector (light)

Distance 6.51 km · énergie 9.6 Wh sur 36.4 Wh utilisables · coût 4.8 pts.

- t = 460 s · engage **C41** (hostile, 65 pts, fenêtre 427–618 s)

### L23 · effector (light)

Distance 5.32 km · énergie 9.0 Wh sur 30.3 Wh utilisables · coût 4.5 pts.

- t = 320 s · engage **C48** (hostile, 83 pts, fenêtre 138–496 s)

### L24 · effector (light)

Distance 5.31 km · énergie 9.2 Wh sur 42.9 Wh utilisables · coût 4.6 pts.

- t = 315 s · engage **C48** (hostile, 83 pts, fenêtre 138–496 s)

### L27 · effector (light)

Distance 5.66 km · énergie 9.5 Wh sur 43.1 Wh utilisables · coût 4.8 pts.

- t = 513 s · engage **C32** (hostile, 67 pts, fenêtre 346–685 s)

### L28 · effector (light)

Distance 5.65 km · énergie 10.0 Wh sur 44.0 Wh utilisables · coût 5.0 pts.

- t = 516 s · engage **C32** (hostile, 67 pts, fenêtre 346–685 s)

### L29 · effector (light)

Distance 6.91 km · énergie 10.9 Wh sur 34.3 Wh utilisables · coût 5.4 pts.

- t = 427 s · engage **C30** (hostile, 60 pts, fenêtre 130–471 s)

### L31 · effector (light)

Distance 6.51 km · énergie 11.3 Wh sur 40.6 Wh utilisables · coût 5.6 pts.

- t = 464 s · engage **C41** (hostile, 65 pts, fenêtre 427–618 s)

### L32 · effector (light)

Distance 5.51 km · énergie 9.0 Wh sur 36.3 Wh utilisables · coût 4.5 pts.

- t = 289 s · engage **C47** (hostile, 97 pts, fenêtre 13–295 s)

### L33 · effector (light)

Distance 5.56 km · énergie 10.1 Wh sur 36.1 Wh utilisables · coût 5.0 pts.

- t = 338 s · engage **C43** (hostile, 95 pts, fenêtre 136–490 s)

### L35 · effector (light)

Distance 5.29 km · énergie 10.3 Wh sur 40.6 Wh utilisables · coût 5.1 pts.

- t = 558 s · engage **C12** (hostile, 65 pts, fenêtre 407–656 s)

### L46 · effector (light)

Distance 6.01 km · énergie 10.2 Wh sur 40.3 Wh utilisables · coût 5.1 pts.

- t = 568 s · engage **C07** (hostile, 80 pts, fenêtre 456–708 s)

### L48 · effector (light)

Distance 6.01 km · énergie 9.2 Wh sur 48.4 Wh utilisables · coût 4.6 pts.

- t = 573 s · engage **C07** (hostile, 80 pts, fenêtre 456–708 s)

### L49 · effector (light)

Distance 5.89 km · énergie 9.7 Wh sur 33.1 Wh utilisables · coût 4.9 pts.

- t = 590 s · engage **C08** (hostile, 56 pts, fenêtre 352–693 s)

### S01 · scout

Distance 13.73 km · énergie 37.1 Wh sur 37.2 Wh utilisables · coût 18.5 pts.

- t = 391 s · observe **C16** (hostile, 61 pts, fenêtre 365–604 s)
- t = 427 s · observe **C41** (hostile, 65 pts, fenêtre 427–618 s)
- t = 518 s · observe **C27** (hostile, 72 pts, fenêtre 471–766 s)
- t = 553 s · observe **C08** (hostile, 56 pts, fenêtre 352–693 s)

### S02 · scout

Distance 11.18 km · énergie 34.1 Wh sur 34.7 Wh utilisables · coût 17.1 pts.

- t = 282 s · observe **C48** (hostile, 83 pts, fenêtre 138–496 s)
- t = 367 s · observe **C52** (unknown, 12 pts, fenêtre 310–566 s)

### S03 · scout

Distance 14.46 km · énergie 34.2 Wh sur 42.1 Wh utilisables · coût 17.1 pts.

- t = 373 s · observe **C40** (hostile, 79 pts, fenêtre 234–576 s)
- t = 449 s · observe **C05** (hostile, 54 pts, fenêtre 314–563 s)
- t = 533 s · observe **C67** (unknown, 19 pts, fenêtre 435–786 s)
- t = 746 s · observe **C54** (unknown, 14 pts, fenêtre 454–787 s)

### S04 · scout

Distance 11.87 km · énergie 26.8 Wh sur 40.1 Wh utilisables · coût 13.4 pts.

- t = 478 s · observe **C23** (hostile, 79 pts, fenêtre 478–758 s)
- t = 536 s · observe **C07** (hostile, 80 pts, fenêtre 456–708 s)

### S05 · scout

Distance 14.16 km · énergie 38.2 Wh sur 38.3 Wh utilisables · coût 19.1 pts.

- t = 335 s · observe **C20** (hostile, 86 pts, fenêtre 198–440 s)
- t = 389 s · observe **C30** (hostile, 60 pts, fenêtre 130–471 s)
- t = 415 s · observe **C64** (unknown, 23 pts, fenêtre 233–436 s)

### S06 · scout

Distance 14.10 km · énergie 43.1 Wh sur 45.6 Wh utilisables · coût 21.6 pts.

- t = 251 s · observe **C47** (hostile, 97 pts, fenêtre 13–295 s)
- t = 295 s · observe **C43** (hostile, 95 pts, fenêtre 136–490 s)
- t = 372 s · observe **C36** (hostile, 47 pts, fenêtre 368–722 s)
- t = 426 s · observe **C17** (hostile, 63 pts, fenêtre 389–666 s)
- t = 476 s · observe **C32** (hostile, 67 pts, fenêtre 346–685 s)
- t = 521 s · observe **C12** (hostile, 65 pts, fenêtre 407–656 s)
- t = 658 s · observe **C61** (unknown, 22 pts, fenêtre 493–759 s)

### S07 · scout

Distance 12.23 km · énergie 32.1 Wh sur 33.6 Wh utilisables · coût 16.0 pts.

- t = 374 s · observe **C38** (hostile, 92 pts, fenêtre 374–605 s)

## Contacts non servis

- **C18** · hostile, 99 pts, besoin : 1 heavy, fenêtre 130–352 s · interdit par R7 (à 132 m de C73, friendly)
- **C01** · hostile, 98 pts, besoin : 2 light, fenêtre 88–386 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C24** · hostile, 97 pts, besoin : 1 light, 2 heavy, fenêtre 318–598 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C13** · hostile, 95 pts, besoin : 4 light, fenêtre 17–237 s · interdit par R7 (à 153 m de C74, friendly)
- **C46** · hostile, 93 pts, besoin : 2 light, fenêtre 449–654 s · interdit par R7 (à 193 m de C88, civilian)
- **C26** · hostile, 92 pts, besoin : 2 heavy, fenêtre 380–732 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C31** · hostile, 90 pts, besoin : 2 light, fenêtre 301–483 s · interdit par R7 (à 164 m de C88, civilian)
- **C06** · hostile, 86 pts, besoin : 1 light, fenêtre 388–612 s · interdit par R7 (à 176 m de C78, friendly)
- **C09** · hostile, 85 pts, besoin : 2 light, 2 heavy, fenêtre 447–763 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C10** · hostile, 85 pts, besoin : 3 light, fenêtre 87–369 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C04** · hostile, 84 pts, besoin : 3 light, 1 heavy, fenêtre 407–656 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C49** · hostile, 84 pts, besoin : 4 light, fenêtre 318–537 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C39** · hostile, 79 pts, besoin : 3 light, fenêtre 222–550 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C03** · hostile, 78 pts, besoin : 1 heavy, fenêtre 75–284 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C22** · hostile, 76 pts, besoin : 2 light, fenêtre 397–614 s · interdit par R7 (à 84 m de C74, friendly)
- **C29** · hostile, 74 pts, besoin : 2 light, fenêtre 56–371 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C02** · hostile, 70 pts, besoin : 1 light, 1 heavy, fenêtre 145–358 s · interdit par R7 (à 113 m de C77, friendly)
- **C34** · hostile, 68 pts, besoin : 2 light, fenêtre 265–566 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C21** · hostile, 67 pts, besoin : 4 light, fenêtre 432–677 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C15** · hostile, 65 pts, besoin : 2 heavy, fenêtre 59–392 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C33** · hostile, 64 pts, besoin : 1 light, 2 heavy, fenêtre 187–456 s · interdit par R7 (à 181 m de C76, friendly)
- **C14** · hostile, 62 pts, besoin : 2 heavy, fenêtre 140–493 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C45** · hostile, 52 pts, besoin : 1 heavy, fenêtre 444–702 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C19** · hostile, 49 pts, besoin : 2 light, fenêtre 454–706 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C35** · hostile, 47 pts, besoin : 3 light, fenêtre 293–590 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C42** · hostile, 47 pts, besoin : 1 heavy, fenêtre 340–623 s · interdit par R7 (à 119 m de C74, friendly)
- **C44** · hostile, 45 pts, besoin : 1 heavy, fenêtre 49–317 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C50** · hostile, 45 pts, besoin : 4 light, fenêtre 482–694 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C11** · hostile, 41 pts, besoin : 3 light, fenêtre 410–678 s · interdit par R7 (à 113 m de C88, civilian)
- **C25** · hostile, 40 pts, besoin : 1 light, fenêtre 79–290 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C28** · hostile, 40 pts, besoin : 1 light, fenêtre 32–272 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C37** · hostile, 40 pts, besoin : 3 light, fenêtre 470–725 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C69** · unknown, 30 pts, besoin : observation, fenêtre 275–542 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C56** · unknown, 29 pts, besoin : observation, fenêtre 230–543 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C59** · unknown, 29 pts, besoin : observation, fenêtre 495–775 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C62** · unknown, 27 pts, besoin : observation, fenêtre 156–462 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C66** · unknown, 27 pts, besoin : observation, fenêtre 280–497 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C55** · unknown, 26 pts, besoin : observation, fenêtre 196–508 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C57** · unknown, 22 pts, besoin : observation, fenêtre 57–402 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C60** · unknown, 21 pts, besoin : observation, fenêtre 394–607 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C53** · unknown, 19 pts, besoin : observation, fenêtre 391–697 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C68** · unknown, 19 pts, besoin : observation, fenêtre 465–774 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C65** · unknown, 13 pts, besoin : observation, fenêtre 110–393 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C51** · unknown, 12 pts, besoin : observation, fenêtre 494–768 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C58** · unknown, 12 pts, besoin : observation, fenêtre 301–490 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C63** · unknown, 11 pts, besoin : observation, fenêtre 450–747 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C70** · unknown, 10 pts, besoin : observation, fenêtre 471–710 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **378 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **0 pts** (gagnable seulement en sacrifiant un autre contact).
