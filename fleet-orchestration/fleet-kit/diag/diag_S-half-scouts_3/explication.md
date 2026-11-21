# Explication du plan · scénario S-half-scouts seed 3

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 292.0 | 679.0 |
| Points servis | 682.0 | 1332.0 |
| Énergie (Wh) | 380.1 | 605.9 |
| Drones d'action consommés | 20 | 35 |
| Contacts servis | 12 | 26 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+133 %** par rapport au glouton (292.0 → 679.0 pts).

Gagnés par rapport au glouton : C01, C02, C05, C09, C13, C21, C25, C29, C33, C45, C48, C53, C60, C61, C63 · perdus : C27.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 13 | 22 |
| effector (light) | 50 | 22 | 28 |
| scout | 7 | 7 | 0 |

Drones au sol : H01, H03, H04, H05, H06, H07, H10, H11, H13, H16, H19, H20, H21, H22, H24, H25, H26, H29, H30, H31, H32, H33, L01, L04, L05, L07, L08, L09, L10, L12, L14, L15, L17, L23, L27, L28, L30, L32, L33, L35, L36, L37, L38, L39, L40, L41, L42, L43, L44, L49.

## Affectations, drone par drone

### H02 · effector (heavy)

Distance 4.16 km · énergie 13.6 Wh sur 53.0 Wh utilisables · coût 6.8 pts.

- t = 411 s · engage **C41** (hostile, 98 pts, fenêtre 334–654 s)

### H08 · effector (heavy)

Distance 3.75 km · énergie 12.6 Wh sur 58.0 Wh utilisables · coût 6.3 pts.

- t = 263 s · engage **C21** (hostile, 66 pts, fenêtre 22–354 s)

### H09 · effector (heavy)

Distance 4.53 km · énergie 11.1 Wh sur 56.0 Wh utilisables · coût 5.5 pts.

- t = 322 s · engage **C29** (hostile, 45 pts, fenêtre 209–403 s)

### H12 · effector (heavy)

Distance 5.50 km · énergie 17.5 Wh sur 59.0 Wh utilisables · coût 8.8 pts.

- t = 464 s · engage **C48** (hostile, 60 pts, fenêtre 431–720 s)

### H14 · effector (heavy)

Distance 6.41 km · énergie 17.1 Wh sur 63.0 Wh utilisables · coût 8.6 pts.

- t = 555 s · engage **C23** (hostile, 51 pts, fenêtre 450–773 s)

### H15 · effector (heavy)

Distance 4.80 km · énergie 13.2 Wh sur 56.1 Wh utilisables · coût 6.6 pts.

- t = 459 s · engage **C25** (hostile, 58 pts, fenêtre 427–750 s)

### H17 · effector (heavy)

Distance 6.00 km · énergie 22.0 Wh sur 68.9 Wh utilisables · coût 11.0 pts.

- t = 439 s · engage **C36** (hostile, 80 pts, fenêtre 346–685 s)

### H18 · effector (heavy)

Distance 4.85 km · énergie 14.2 Wh sur 52.8 Wh utilisables · coût 7.1 pts.

- t = 537 s · engage **C05** (hostile, 45 pts, fenêtre 397–578 s)

### H23 · effector (heavy)

Distance 5.99 km · énergie 22.1 Wh sur 51.0 Wh utilisables · coût 11.0 pts.

- t = 434 s · engage **C36** (hostile, 80 pts, fenêtre 346–685 s)

### H27 · effector (heavy)

Distance 4.70 km · énergie 14.3 Wh sur 45.0 Wh utilisables · coût 7.1 pts.

- t = 640 s · engage **C45** (hostile, 73 pts, fenêtre 451–738 s)

### H28 · effector (heavy)

Distance 6.21 km · énergie 21.9 Wh sur 55.9 Wh utilisables · coût 11.0 pts.

- t = 468 s · engage **C24** (hostile, 76 pts, fenêtre 436–684 s)

### H34 · effector (heavy)

Distance 4.85 km · énergie 14.5 Wh sur 58.9 Wh utilisables · coût 7.3 pts.

- t = 381 s · engage **C01** (hostile, 42 pts, fenêtre 338–618 s)

### H35 · effector (heavy)

Distance 3.76 km · énergie 11.4 Wh sur 52.4 Wh utilisables · coût 5.7 pts.

- t = 268 s · engage **C21** (hostile, 66 pts, fenêtre 22–354 s)

### L02 · effector (light)

Distance 4.53 km · énergie 8.2 Wh sur 30.7 Wh utilisables · coût 4.1 pts.

- t = 664 s · engage **C13** (hostile, 72 pts, fenêtre 369–721 s)

### L03 · effector (light)

Distance 4.48 km · énergie 8.5 Wh sur 38.6 Wh utilisables · coût 4.3 pts.

- t = 568 s · engage **C17** (hostile, 74 pts, fenêtre 475–828 s)

### L06 · effector (light)

Distance 4.71 km · énergie 8.1 Wh sur 33.5 Wh utilisables · coût 4.0 pts.

- t = 645 s · engage **C45** (hostile, 73 pts, fenêtre 451–738 s)

### L11 · effector (light)

Distance 4.32 km · énergie 6.7 Wh sur 33.1 Wh utilisables · coût 3.3 pts.

- t = 358 s · engage **C09** (hostile, 59 pts, fenêtre 321–510 s)

### L13 · effector (light)

Distance 4.78 km · énergie 7.7 Wh sur 40.9 Wh utilisables · coût 3.8 pts.

- t = 489 s · engage **C33** (hostile, 41 pts, fenêtre 252–503 s)

### L16 · effector (light)

Distance 6.20 km · énergie 11.8 Wh sur 38.7 Wh utilisables · coût 5.9 pts.

- t = 478 s · engage **C24** (hostile, 76 pts, fenêtre 436–684 s)

### L18 · effector (light)

Distance 4.21 km · énergie 6.6 Wh sur 40.8 Wh utilisables · coût 3.3 pts.

- t = 686 s · engage **C37** (hostile, 93 pts, fenêtre 470–817 s)

### L19 · effector (light)

Distance 4.24 km · énergie 8.3 Wh sur 36.3 Wh utilisables · coût 4.1 pts.

- t = 696 s · engage **C37** (hostile, 93 pts, fenêtre 470–817 s)

### L20 · effector (light)

Distance 5.49 km · énergie 8.3 Wh sur 33.2 Wh utilisables · coût 4.1 pts.

- t = 468 s · engage **C48** (hostile, 60 pts, fenêtre 431–720 s)

### L21 · effector (light)

Distance 4.22 km · énergie 8.6 Wh sur 31.9 Wh utilisables · coût 4.3 pts.

- t = 691 s · engage **C37** (hostile, 93 pts, fenêtre 470–817 s)

### L22 · effector (light)

Distance 4.30 km · énergie 7.1 Wh sur 35.0 Wh utilisables · coût 3.5 pts.

- t = 353 s · engage **C09** (hostile, 59 pts, fenêtre 321–510 s)

### L24 · effector (light)

Distance 4.47 km · énergie 7.8 Wh sur 43.0 Wh utilisables · coût 3.9 pts.

- t = 556 s · engage **C17** (hostile, 74 pts, fenêtre 475–828 s)

### L25 · effector (light)

Distance 4.52 km · énergie 7.5 Wh sur 41.5 Wh utilisables · coût 3.7 pts.

- t = 659 s · engage **C13** (hostile, 72 pts, fenêtre 369–721 s)

### L26 · effector (light)

Distance 4.20 km · énergie 6.1 Wh sur 33.1 Wh utilisables · coût 3.1 pts.

- t = 681 s · engage **C37** (hostile, 93 pts, fenêtre 470–817 s)

### L29 · effector (light)

Distance 4.18 km · énergie 6.6 Wh sur 48.6 Wh utilisables · coût 3.3 pts.

- t = 416 s · engage **C41** (hostile, 98 pts, fenêtre 334–654 s)

### L31 · effector (light)

Distance 4.51 km · énergie 6.4 Wh sur 50.4 Wh utilisables · coût 3.2 pts.

- t = 654 s · engage **C13** (hostile, 72 pts, fenêtre 369–721 s)

### L34 · effector (light)

Distance 6.19 km · énergie 11.8 Wh sur 45.0 Wh utilisables · coût 5.9 pts.

- t = 480 s · engage **C24** (hostile, 76 pts, fenêtre 436–684 s)

### L45 · effector (light)

Distance 7.61 km · énergie 12.3 Wh sur 41.5 Wh utilisables · coût 6.2 pts.

- t = 450 s · engage **C02** (hostile, 95 pts, fenêtre 344–534 s)

### L46 · effector (light)

Distance 4.73 km · énergie 9.1 Wh sur 34.9 Wh utilisables · coût 4.6 pts.

- t = 655 s · engage **C45** (hostile, 73 pts, fenêtre 451–738 s)

### L47 · effector (light)

Distance 4.49 km · énergie 10.2 Wh sur 36.5 Wh utilisables · coût 5.1 pts.

- t = 566 s · engage **C17** (hostile, 74 pts, fenêtre 475–828 s)

### L48 · effector (light)

Distance 4.47 km · énergie 7.3 Wh sur 39.8 Wh utilisables · coût 3.7 pts.

- t = 558 s · engage **C17** (hostile, 74 pts, fenêtre 475–828 s)

### L50 · effector (light)

Distance 4.72 km · énergie 8.7 Wh sur 39.9 Wh utilisables · coût 4.3 pts.

- t = 650 s · engage **C45** (hostile, 73 pts, fenêtre 451–738 s)

### S01 · scout

Distance 12.29 km · énergie 31.4 Wh sur 38.1 Wh utilisables · coût 15.7 pts.

- t = 403 s · observe **C36** (hostile, 80 pts, fenêtre 346–685 s)
- t = 436 s · observe **C24** (hostile, 76 pts, fenêtre 436–684 s)

### S02 · scout

Distance 11.81 km · énergie 27.6 Wh sur 31.6 Wh utilisables · coût 13.8 pts.

- t = 431 s · observe **C48** (hostile, 60 pts, fenêtre 431–720 s)
- t = 501 s · observe **C05** (hostile, 45 pts, fenêtre 397–578 s)
- t = 548 s · observe **C61** (unknown, 23 pts, fenêtre 470–800 s)

### S03 · scout

Distance 11.47 km · énergie 31.4 Wh sur 35.1 Wh utilisables · coût 15.7 pts.

- t = 231 s · observe **C21** (hostile, 66 pts, fenêtre 22–354 s)
- t = 321 s · observe **C09** (hostile, 59 pts, fenêtre 321–510 s)
- t = 368 s · observe **C41** (hostile, 98 pts, fenêtre 334–654 s)
- t = 428 s · observe **C25** (hostile, 58 pts, fenêtre 427–750 s)
- t = 454 s · observe **C33** (hostile, 41 pts, fenêtre 252–503 s)
- t = 525 s · observe **C17** (hostile, 74 pts, fenêtre 475–828 s)
- t = 555 s · observe **C45** (hostile, 73 pts, fenêtre 451–738 s)
- t = 576 s · observe **C13** (hostile, 72 pts, fenêtre 369–721 s)
- t = 649 s · observe **C37** (hostile, 93 pts, fenêtre 470–817 s)

### S04 · scout

Distance 15.51 km · énergie 42.9 Wh sur 44.3 Wh utilisables · coût 21.4 pts.

- t = 418 s · observe **C02** (hostile, 95 pts, fenêtre 344–534 s)
- t = 523 s · observe **C23** (hostile, 51 pts, fenêtre 450–773 s)

### S05 · scout

Distance 8.86 km · énergie 27.4 Wh sur 28.7 Wh utilisables · coût 13.7 pts.

- t = 245 s · observe **C53** (unknown, 25 pts, fenêtre 245–490 s)
- t = 295 s · observe **C63** (unknown, 22 pts, fenêtre 177–457 s)
- t = 381 s · observe **C60** (unknown, 17 pts, fenêtre 261–596 s)

### S06 · scout

Distance 8.99 km · énergie 24.1 Wh sur 26.3 Wh utilisables · coût 12.0 pts.

- t = 315 s · observe **C56** (unknown, 30 pts, fenêtre 204–403 s)
- t = 371 s · observe **C59** (unknown, 28 pts, fenêtre 269–461 s)
- t = 424 s · observe **C66** (unknown, 27 pts, fenêtre 424–612 s)
- t = 470 s · observe **C51** (unknown, 17 pts, fenêtre 362–699 s)
- t = 616 s · observe **C54** (unknown, 15 pts, fenêtre 482–740 s)

### S07 · scout

Distance 9.91 km · énergie 32.1 Wh sur 32.4 Wh utilisables · coût 16.0 pts.

- t = 290 s · observe **C29** (hostile, 45 pts, fenêtre 209–403 s)
- t = 349 s · observe **C01** (hostile, 42 pts, fenêtre 338–618 s)

## Contacts non servis

- **C19** · hostile, 98 pts, besoin : 1 light, fenêtre 488–809 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C50** · hostile, 98 pts, besoin : 3 light, fenêtre 175–521 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C27** · hostile, 93 pts, besoin : 2 light, 2 heavy, fenêtre 145–500 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C39** · hostile, 93 pts, besoin : 4 light, fenêtre 239–594 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C49** · hostile, 93 pts, besoin : 2 heavy, fenêtre 152–472 s · interdit par R7 (à 154 m de C78, friendly)
- **C08** · hostile, 91 pts, besoin : 2 light, fenêtre 65–392 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C20** · hostile, 90 pts, besoin : 1 heavy, fenêtre 320–526 s · interdit par R7 (à 172 m de C76, friendly)
- **C40** · hostile, 90 pts, besoin : 2 light, fenêtre 254–528 s · interdit par R7 (à 186 m de C87, civilian)
- **C03** · hostile, 89 pts, besoin : 1 heavy, fenêtre 30–388 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C18** · hostile, 85 pts, besoin : 1 light, fenêtre 141–401 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C07** · hostile, 84 pts, besoin : 3 light, fenêtre 491–741 s · interdit par R7 (à 184 m de C79, friendly)
- **C30** · hostile, 82 pts, besoin : 2 light, fenêtre 403–685 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C42** · hostile, 81 pts, besoin : 1 light, fenêtre 28–353 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C15** · hostile, 80 pts, besoin : 1 light, fenêtre 146–432 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C35** · hostile, 77 pts, besoin : 1 heavy, fenêtre 174–514 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C31** · hostile, 76 pts, besoin : 2 light, fenêtre 368–579 s · interdit par R7 (à 111 m de C71, friendly)
- **C44** · hostile, 76 pts, besoin : 1 light, fenêtre 414–643 s · interdit par R7 (à 163 m de C87, civilian)
- **C22** · hostile, 72 pts, besoin : 1 light, fenêtre 335–635 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C10** · hostile, 71 pts, besoin : 2 light, 2 heavy, fenêtre 71–386 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C28** · hostile, 66 pts, besoin : 1 light, 2 heavy, fenêtre 153–427 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C26** · hostile, 64 pts, besoin : 2 light, 1 heavy, fenêtre 234–552 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C34** · hostile, 64 pts, besoin : 4 light, fenêtre 247–473 s · interdit par R7 (à 154 m de C82, friendly)
- **C12** · hostile, 63 pts, besoin : 2 light, fenêtre 303–534 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C47** · hostile, 63 pts, besoin : 1 light, fenêtre 427–694 s · interdit par R7 (à 131 m de C90, civilian)
- **C04** · hostile, 61 pts, besoin : 4 light, fenêtre 200–386 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C46** · hostile, 58 pts, besoin : 1 light, 1 heavy, fenêtre 48–400 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C43** · hostile, 56 pts, besoin : 1 light, fenêtre 131–349 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C11** · hostile, 55 pts, besoin : 2 light, fenêtre 337–563 s · interdit par R7 (à 183 m de C79, friendly)
- **C32** · hostile, 47 pts, besoin : 2 light, fenêtre 119–479 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C14** · hostile, 43 pts, besoin : 1 light, fenêtre 378–721 s · interdit par R7 (à 141 m de C83, civilian)
- **C06** · hostile, 42 pts, besoin : 3 light, 1 heavy, fenêtre 140–392 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C38** · hostile, 42 pts, besoin : 1 heavy, fenêtre 334–552 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C16** · hostile, 40 pts, besoin : 2 light, 1 heavy, fenêtre 91–307 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C58** · unknown, 22 pts, besoin : observation, fenêtre 487–685 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C64** · unknown, 21 pts, besoin : observation, fenêtre 457–810 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C52** · unknown, 20 pts, besoin : observation, fenêtre 245–580 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C68** · unknown, 20 pts, besoin : observation, fenêtre 66–357 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C67** · unknown, 18 pts, besoin : observation, fenêtre 26–322 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C57** · unknown, 17 pts, besoin : observation, fenêtre 380–571 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C55** · unknown, 16 pts, besoin : observation, fenêtre 123–386 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C62** · unknown, 13 pts, besoin : observation, fenêtre 40–297 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C69** · unknown, 11 pts, besoin : observation, fenêtre 95–378 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C65** · unknown, 10 pts, besoin : observation, fenêtre 11–309 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C70** · unknown, 10 pts, besoin : observation, fenêtre 103–326 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **496 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **0 pts** (gagnable seulement en sacrifiant un autre contact).
