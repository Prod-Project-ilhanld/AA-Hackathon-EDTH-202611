# Explication du plan · scénario L4 seed 3

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 532.9 | 1064.6 |
| Points servis | 1140.0 | 2207.0 |
| Énergie (Wh) | 514.2 | 1024.9 |
| Drones d'action consommés | 35 | 63 |
| Contacts servis | 18 | 39 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+100 %** par rapport au glouton (532.9 → 1064.6 pts).

Gagnés par rapport au glouton : C04, C05, C07, C14, C17, C22, C24, C30, C32, C33, C34, C35, C46, C51, C52, C56, C61, C63, C67, C68, C69 · perdus : aucun.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 13 | 22 |
| effector (light) | 50 | 50 | 0 |
| scout | 15 | 14 | 1 |

Drones au sol : H04, H05, H06, H07, H08, H09, H10, H15, H16, H17, H18, H20, H22, H23, H24, H25, H26, H27, H28, H29, H32, H35, S08.

## Affectations, drone par drone

### H01 · effector (heavy)

Distance 3.58 km · énergie 11.6 Wh sur 51.5 Wh utilisables · coût 5.8 pts.

- t = 653 s · engage **C41** (hostile, 75 pts, fenêtre 480–693 s)

### H02 · effector (heavy)

Distance 3.58 km · énergie 11.8 Wh sur 49.6 Wh utilisables · coût 5.9 pts.

- t = 685 s · engage **C47** (hostile, 62 pts, fenêtre 445–795 s)

### H03 · effector (heavy)

Distance 6.13 km · énergie 15.6 Wh sur 53.0 Wh utilisables · coût 7.8 pts.

- t = 405 s · engage **C04** (hostile, 54 pts, fenêtre 229–464 s)

### H11 · effector (heavy)

Distance 2.20 km · énergie 7.4 Wh sur 50.0 Wh utilisables · coût 3.7 pts.

- t = 329 s · engage **C35** (hostile, 78 pts, fenêtre 171–503 s)

### H12 · effector (heavy)

Distance 3.03 km · énergie 10.2 Wh sur 55.9 Wh utilisables · coût 5.1 pts.

- t = 643 s · engage **C38** (hostile, 77 pts, fenêtre 410–680 s)

### H13 · effector (heavy)

Distance 6.46 km · énergie 21.1 Wh sur 52.8 Wh utilisables · coût 10.6 pts.

- t = 451 s · engage **C39** (hostile, 98 pts, fenêtre 309–581 s)

### H14 · effector (heavy)

Distance 2.18 km · énergie 7.9 Wh sur 52.0 Wh utilisables · coût 3.9 pts.

- t = 331 s · engage **C35** (hostile, 78 pts, fenêtre 171–503 s)

### H19 · effector (heavy)

Distance 5.91 km · énergie 17.0 Wh sur 43.5 Wh utilisables · coût 8.5 pts.

- t = 542 s · engage **C33** (hostile, 63 pts, fenêtre 464–739 s)

### H21 · effector (heavy)

Distance 3.01 km · énergie 7.4 Wh sur 43.8 Wh utilisables · coût 3.7 pts.

- t = 638 s · engage **C38** (hostile, 77 pts, fenêtre 410–680 s)

### H30 · effector (heavy)

Distance 3.60 km · énergie 11.1 Wh sur 62.6 Wh utilisables · coût 5.5 pts.

- t = 651 s · engage **C41** (hostile, 75 pts, fenêtre 480–693 s)

### H31 · effector (heavy)

Distance 6.47 km · énergie 19.3 Wh sur 54.8 Wh utilisables · coût 9.6 pts.

- t = 456 s · engage **C39** (hostile, 98 pts, fenêtre 309–581 s)

### H33 · effector (heavy)

Distance 4.66 km · énergie 18.4 Wh sur 61.6 Wh utilisables · coût 9.2 pts.

- t = 514 s · engage **C24** (hostile, 54 pts, fenêtre 334–577 s)

### H34 · effector (heavy)

Distance 2.57 km · énergie 10.3 Wh sur 56.3 Wh utilisables · coût 5.2 pts.

- t = 359 s · engage **C26** (hostile, 80 pts, fenêtre 245–503 s)

### L01 · effector (light)

Distance 5.98 km · énergie 9.4 Wh sur 51.2 Wh utilisables · coût 4.7 pts.

- t = 547 s · engage **C33** (hostile, 63 pts, fenêtre 464–739 s)

### L02 · effector (light)

Distance 3.58 km · énergie 6.0 Wh sur 45.8 Wh utilisables · coût 3.0 pts.

- t = 695 s · engage **C47** (hostile, 62 pts, fenêtre 445–795 s)

### L03 · effector (light)

Distance 5.12 km · énergie 8.4 Wh sur 30.0 Wh utilisables · coût 4.2 pts.

- t = 504 s · engage **C12** (hostile, 82 pts, fenêtre 431–637 s)

### L04 · effector (light)

Distance 2.99 km · énergie 6.4 Wh sur 45.1 Wh utilisables · coût 3.2 pts.

- t = 559 s · engage **C14** (hostile, 73 pts, fenêtre 360–630 s)

### L05 · effector (light)

Distance 2.59 km · énergie 6.0 Wh sur 36.0 Wh utilisables · coût 3.0 pts.

- t = 364 s · engage **C26** (hostile, 80 pts, fenêtre 245–503 s)

### L06 · effector (light)

Distance 4.66 km · énergie 6.9 Wh sur 40.1 Wh utilisables · coût 3.4 pts.

- t = 451 s · engage **C42** (hostile, 96 pts, fenêtre 151–464 s)

### L07 · effector (light)

Distance 4.22 km · énergie 8.2 Wh sur 33.4 Wh utilisables · coût 4.1 pts.

- t = 541 s · engage **C05** (hostile, 66 pts, fenêtre 339–546 s)

### L08 · effector (light)

Distance 4.63 km · énergie 8.3 Wh sur 36.4 Wh utilisables · coût 4.2 pts.

- t = 540 s · engage **C18** (hostile, 89 pts, fenêtre 408–672 s)

### L09 · effector (light)

Distance 7.26 km · énergie 13.8 Wh sur 48.0 Wh utilisables · coût 6.9 pts.

- t = 470 s · engage **C34** (hostile, 50 pts, fenêtre 187–477 s)

### L10 · effector (light)

Distance 3.59 km · énergie 7.7 Wh sur 37.1 Wh utilisables · coût 3.9 pts.

- t = 700 s · engage **C47** (hostile, 62 pts, fenêtre 445–795 s)

### L11 · effector (light)

Distance 2.36 km · énergie 4.8 Wh sur 44.7 Wh utilisables · coût 2.4 pts.

- t = 398 s · engage **C08** (hostile, 93 pts, fenêtre 131–435 s)

### L12 · effector (light)

Distance 2.83 km · énergie 4.4 Wh sur 29.3 Wh utilisables · coût 2.2 pts.

- t = 669 s · engage **C44** (hostile, 54 pts, fenêtre 452–770 s)

### L13 · effector (light)

Distance 5.12 km · énergie 9.5 Wh sur 38.9 Wh utilisables · coût 4.7 pts.

- t = 505 s · engage **C12** (hostile, 82 pts, fenêtre 431–637 s)

### L14 · effector (light)

Distance 5.11 km · énergie 7.5 Wh sur 36.8 Wh utilisables · coût 3.8 pts.

- t = 494 s · engage **C12** (hostile, 82 pts, fenêtre 431–637 s)

### L15 · effector (light)

Distance 4.31 km · énergie 9.1 Wh sur 46.1 Wh utilisables · coût 4.5 pts.

- t = 446 s · engage **C30** (hostile, 62 pts, fenêtre 266–459 s)

### L16 · effector (light)

Distance 6.03 km · énergie 9.9 Wh sur 40.5 Wh utilisables · coût 4.9 pts.

- t = 392 s · engage **C45** (hostile, 85 pts, fenêtre 360–633 s)

### L17 · effector (light)

Distance 2.79 km · énergie 5.6 Wh sur 37.0 Wh utilisables · coût 2.8 pts.

- t = 218 s · engage **C02** (hostile, 97 pts, fenêtre 106–301 s)

### L18 · effector (light)

Distance 2.34 km · énergie 4.4 Wh sur 44.7 Wh utilisables · coût 2.2 pts.

- t = 393 s · engage **C08** (hostile, 93 pts, fenêtre 131–435 s)

### L19 · effector (light)

Distance 4.63 km · énergie 9.4 Wh sur 43.8 Wh utilisables · coût 4.7 pts.

- t = 550 s · engage **C18** (hostile, 89 pts, fenêtre 408–672 s)

### L20 · effector (light)

Distance 4.31 km · énergie 7.9 Wh sur 44.4 Wh utilisables · coût 4.0 pts.

- t = 451 s · engage **C30** (hostile, 62 pts, fenêtre 266–459 s)

### L21 · effector (light)

Distance 7.41 km · énergie 11.0 Wh sur 36.5 Wh utilisables · coût 5.5 pts.

- t = 505 s · engage **C46** (hostile, 91 pts, fenêtre 473–709 s)

### L22 · effector (light)

Distance 3.60 km · énergie 7.0 Wh sur 34.0 Wh utilisables · coût 3.5 pts.

- t = 656 s · engage **C41** (hostile, 75 pts, fenêtre 480–693 s)

### L23 · effector (light)

Distance 2.38 km · énergie 4.7 Wh sur 43.7 Wh utilisables · coût 2.4 pts.

- t = 403 s · engage **C08** (hostile, 93 pts, fenêtre 131–435 s)

### L24 · effector (light)

Distance 4.23 km · énergie 8.2 Wh sur 49.5 Wh utilisables · coût 4.1 pts.

- t = 546 s · engage **C05** (hostile, 66 pts, fenêtre 339–546 s)

### L25 · effector (light)

Distance 8.31 km · énergie 13.0 Wh sur 34.3 Wh utilisables · coût 6.5 pts.

- t = 474 s · engage **C07** (hostile, 88 pts, fenêtre 402–662 s)

### L26 · effector (light)

Distance 4.67 km · énergie 9.2 Wh sur 48.6 Wh utilisables · coût 4.6 pts.

- t = 450 s · engage **C42** (hostile, 96 pts, fenêtre 151–464 s)

### L27 · effector (light)

Distance 3.57 km · énergie 5.9 Wh sur 32.1 Wh utilisables · coût 2.9 pts.

- t = 696 s · engage **C47** (hostile, 62 pts, fenêtre 445–795 s)

### L28 · effector (light)

Distance 4.74 km · énergie 9.2 Wh sur 47.1 Wh utilisables · coût 4.6 pts.

- t = 518 s · engage **C24** (hostile, 54 pts, fenêtre 334–577 s)

### L29 · effector (light)

Distance 4.66 km · énergie 8.1 Wh sur 31.6 Wh utilisables · coût 4.1 pts.

- t = 445 s · engage **C42** (hostile, 96 pts, fenêtre 151–464 s)

### L30 · effector (light)

Distance 7.04 km · énergie 10.9 Wh sur 39.5 Wh utilisables · coût 5.4 pts.

- t = 441 s · engage **C22** (hostile, 97 pts, fenêtre 326–637 s)

### L31 · effector (light)

Distance 2.98 km · énergie 6.1 Wh sur 48.7 Wh utilisables · coût 3.1 pts.

- t = 554 s · engage **C14** (hostile, 73 pts, fenêtre 360–630 s)

### L32 · effector (light)

Distance 4.24 km · énergie 7.6 Wh sur 35.8 Wh utilisables · coût 3.8 pts.

- t = 536 s · engage **C05** (hostile, 66 pts, fenêtre 339–546 s)

### L33 · effector (light)

Distance 6.49 km · énergie 10.4 Wh sur 31.7 Wh utilisables · coût 5.2 pts.

- t = 461 s · engage **C39** (hostile, 98 pts, fenêtre 309–581 s)

### L34 · effector (light)

Distance 4.63 km · énergie 8.3 Wh sur 30.8 Wh utilisables · coût 4.2 pts.

- t = 545 s · engage **C18** (hostile, 89 pts, fenêtre 408–672 s)

### L35 · effector (light)

Distance 4.30 km · énergie 7.3 Wh sur 45.4 Wh utilisables · coût 3.6 pts.

- t = 456 s · engage **C30** (hostile, 62 pts, fenêtre 266–459 s)

### L36 · effector (light)

Distance 2.77 km · énergie 4.8 Wh sur 35.4 Wh utilisables · coût 2.4 pts.

- t = 208 s · engage **C02** (hostile, 97 pts, fenêtre 106–301 s)

### L37 · effector (light)

Distance 2.78 km · énergie 5.0 Wh sur 41.8 Wh utilisables · coût 2.5 pts.

- t = 600 s · engage **C32** (hostile, 59 pts, fenêtre 280–621 s)

### L38 · effector (light)

Distance 4.64 km · énergie 9.0 Wh sur 41.8 Wh utilisables · coût 4.5 pts.

- t = 555 s · engage **C18** (hostile, 89 pts, fenêtre 408–672 s)

### L39 · effector (light)

Distance 3.01 km · énergie 7.8 Wh sur 35.9 Wh utilisables · coût 3.9 pts.

- t = 564 s · engage **C14** (hostile, 73 pts, fenêtre 360–630 s)

### L40 · effector (light)

Distance 3.70 km · énergie 6.6 Wh sur 46.9 Wh utilisables · coût 3.3 pts.

- t = 540 s · engage **C17** (hostile, 65 pts, fenêtre 299–580 s)

### L41 · effector (light)

Distance 3.90 km · énergie 5.6 Wh sur 44.0 Wh utilisables · coût 2.8 pts.

- t = 500 s · engage **C11** (hostile, 55 pts, fenêtre 459–766 s)

### L42 · effector (light)

Distance 6.05 km · énergie 9.6 Wh sur 42.5 Wh utilisables · coût 4.8 pts.

- t = 398 s · engage **C45** (hostile, 85 pts, fenêtre 360–633 s)

### L43 · effector (light)

Distance 3.85 km · énergie 6.8 Wh sur 31.9 Wh utilisables · coût 3.4 pts.

- t = 506 s · engage **C11** (hostile, 55 pts, fenêtre 459–766 s)

### L44 · effector (light)

Distance 2.78 km · énergie 4.7 Wh sur 44.7 Wh utilisables · coût 2.4 pts.

- t = 216 s · engage **C02** (hostile, 97 pts, fenêtre 106–301 s)

### L45 · effector (light)

Distance 5.99 km · énergie 9.4 Wh sur 42.2 Wh utilisables · coût 4.7 pts.

- t = 552 s · engage **C33** (hostile, 63 pts, fenêtre 464–739 s)

### L46 · effector (light)

Distance 2.81 km · énergie 4.6 Wh sur 38.5 Wh utilisables · coût 2.3 pts.

- t = 605 s · engage **C32** (hostile, 59 pts, fenêtre 280–621 s)

### L47 · effector (light)

Distance 2.83 km · énergie 6.0 Wh sur 42.4 Wh utilisables · coût 3.0 pts.

- t = 610 s · engage **C32** (hostile, 59 pts, fenêtre 280–621 s)

### L48 · effector (light)

Distance 2.17 km · énergie 4.6 Wh sur 37.7 Wh utilisables · coût 2.3 pts.

- t = 334 s · engage **C35** (hostile, 78 pts, fenêtre 171–503 s)

### L49 · effector (light)

Distance 8.32 km · énergie 14.9 Wh sur 39.9 Wh utilisables · coût 7.5 pts.

- t = 479 s · engage **C07** (hostile, 88 pts, fenêtre 402–662 s)

### L50 · effector (light)

Distance 2.96 km · énergie 4.8 Wh sur 35.0 Wh utilisables · coût 2.4 pts.

- t = 549 s · engage **C14** (hostile, 73 pts, fenêtre 360–630 s)

### S01 · scout

Distance 11.74 km · énergie 32.5 Wh sur 44.4 Wh utilisables · coût 16.2 pts.

- t = 176 s · observe **C02** (hostile, 97 pts, fenêtre 106–301 s)
- t = 268 s · observe **C35** (hostile, 78 pts, fenêtre 171–503 s)
- t = 462 s · observe **C12** (hostile, 82 pts, fenêtre 431–637 s)
- t = 509 s · observe **C18** (hostile, 89 pts, fenêtre 408–672 s)
- t = 616 s · observe **C41** (hostile, 75 pts, fenêtre 480–693 s)
- t = 641 s · observe **C47** (hostile, 62 pts, fenêtre 445–795 s)

### S02 · scout

Distance 14.81 km · énergie 40.0 Wh sur 43.4 Wh utilisables · coût 20.0 pts.

- t = 473 s · observe **C46** (hostile, 91 pts, fenêtre 473–709 s)

### S03 · scout

Distance 9.51 km · énergie 27.6 Wh sur 29.6 Wh utilisables · coût 13.8 pts.

- t = 423 s · observe **C05** (hostile, 66 pts, fenêtre 339–546 s)
- t = 459 s · observe **C11** (hostile, 55 pts, fenêtre 459–766 s)
- t = 502 s · observe **C17** (hostile, 65 pts, fenêtre 299–580 s)
- t = 534 s · observe **C54** (unknown, 28 pts, fenêtre 392–733 s)
- t = 586 s · observe **C51** (unknown, 17 pts, fenêtre 392–627 s)

### S04 · scout

Distance 12.89 km · énergie 36.1 Wh sur 37.2 Wh utilisables · coût 18.0 pts.

- t = 149 s · observe **C08** (hostile, 93 pts, fenêtre 131–435 s)
- t = 418 s · observe **C39** (hostile, 98 pts, fenêtre 309–581 s)
- t = 455 s · observe **C56** (unknown, 24 pts, fenêtre 442–692 s)
- t = 575 s · observe **C57** (unknown, 14 pts, fenêtre 398–694 s)

### S05 · scout

Distance 14.42 km · énergie 34.4 Wh sur 48.4 Wh utilisables · coût 17.2 pts.

- t = 400 s · observe **C22** (hostile, 97 pts, fenêtre 326–637 s)
- t = 438 s · observe **C34** (hostile, 50 pts, fenêtre 187–477 s)
- t = 628 s · observe **C63** (unknown, 16 pts, fenêtre 453–803 s)

### S06 · scout

Distance 12.95 km · énergie 36.1 Wh sur 46.0 Wh utilisables · coût 18.0 pts.

- t = 400 s · observe **C52** (unknown, 25 pts, fenêtre 358–648 s)
- t = 477 s · observe **C67** (unknown, 23 pts, fenêtre 413–724 s)

### S07 · scout

Distance 13.47 km · énergie 33.0 Wh sur 39.1 Wh utilisables · coût 16.5 pts.

- t = 375 s · observe **C04** (hostile, 54 pts, fenêtre 229–464 s)
- t = 611 s · observe **C70** (unknown, 10 pts, fenêtre 412–689 s)

### S09 · scout

Distance 8.45 km · énergie 27.7 Wh sur 34.8 Wh utilisables · coût 13.8 pts.

- t = 437 s · observe **C62** (unknown, 23 pts, fenêtre 180–525 s)
- t = 493 s · observe **C53** (unknown, 22 pts, fenêtre 493–779 s)
- t = 599 s · observe **C61** (unknown, 18 pts, fenêtre 345–626 s)

### S10 · scout

Distance 10.24 km · énergie 28.7 Wh sur 29.7 Wh utilisables · coût 14.4 pts.

- t = 312 s · observe **C68** (unknown, 17 pts, fenêtre 184–416 s)

### S11 · scout

Distance 16.52 km · énergie 42.8 Wh sur 45.2 Wh utilisables · coût 21.4 pts.

- t = 442 s · observe **C07** (hostile, 88 pts, fenêtre 402–662 s)

### S12 · scout

Distance 13.30 km · énergie 37.2 Wh sur 39.6 Wh utilisables · coût 18.6 pts.

- t = 283 s · observe **C30** (hostile, 62 pts, fenêtre 266–459 s)
- t = 335 s · observe **C24** (hostile, 54 pts, fenêtre 334–577 s)
- t = 470 s · observe **C69** (unknown, 27 pts, fenêtre 270–606 s)

### S13 · scout

Distance 10.59 km · énergie 30.2 Wh sur 36.0 Wh utilisables · coût 15.1 pts.

- t = 245 s · observe **C26** (hostile, 80 pts, fenêtre 245–503 s)
- t = 407 s · observe **C42** (hostile, 96 pts, fenêtre 151–464 s)
- t = 512 s · observe **C14** (hostile, 73 pts, fenêtre 360–630 s)
- t = 604 s · observe **C38** (hostile, 77 pts, fenêtre 410–680 s)
- t = 636 s · observe **C44** (hostile, 54 pts, fenêtre 452–770 s)

### S14 · scout

Distance 11.91 km · énergie 34.8 Wh sur 36.7 Wh utilisables · coût 17.4 pts.

- t = 360 s · observe **C45** (hostile, 85 pts, fenêtre 360–633 s)
- t = 568 s · observe **C32** (hostile, 59 pts, fenêtre 280–621 s)

### S15 · scout

Distance 11.83 km · énergie 29.8 Wh sur 43.1 Wh utilisables · coût 14.9 pts.

- t = 464 s · observe **C33** (hostile, 63 pts, fenêtre 464–739 s)

## Contacts non servis

- **C37** · hostile, 88 pts, besoin : 3 light, fenêtre 234–429 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C27** · hostile, 85 pts, besoin : 1 light, 2 heavy, fenêtre 98–338 s · interdit par R7 (à 140 m de C84, civilian)
- **C50** · hostile, 84 pts, besoin : 4 light, fenêtre 69–325 s · routable seul, mais les drones nécessaires sont déjà pris par un autre contact dans notre plan (concurrence de ressources)
- **C25** · hostile, 82 pts, besoin : 1 light, 1 heavy, fenêtre 75–412 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C13** · hostile, 79 pts, besoin : 3 light, fenêtre 52–283 s · interdit par R7 (à 114 m de C71, friendly)
- **C43** · hostile, 77 pts, besoin : 4 light, fenêtre 302–513 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C20** · hostile, 75 pts, besoin : 3 light, 1 heavy, fenêtre 99–298 s · routable seul, mais les drones nécessaires sont déjà pris par un autre contact dans notre plan (concurrence de ressources)
- **C09** · hostile, 73 pts, besoin : 2 light, 2 heavy, fenêtre 364–556 s · interdit par R7 (à 114 m de C76, friendly)
- **C15** · hostile, 73 pts, besoin : 1 light, fenêtre 366–602 s · interdit par R7 (à 152 m de C82, friendly)
- **C06** · hostile, 69 pts, besoin : 2 light, 1 heavy, fenêtre 81–300 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C10** · hostile, 66 pts, besoin : 2 heavy, fenêtre 15–212 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C23** · hostile, 66 pts, besoin : 1 light, fenêtre 412–740 s · interdit par R7 (à 170 m de C72, friendly)
- **C49** · hostile, 65 pts, besoin : 3 light, fenêtre 59–340 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C16** · hostile, 63 pts, besoin : 4 light, fenêtre 193–496 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C21** · hostile, 61 pts, besoin : 2 light, 1 heavy, fenêtre 196–453 s · interdit par R7 (à 168 m de C84, civilian)
- **C29** · hostile, 60 pts, besoin : 2 light, 2 heavy, fenêtre 413–764 s · pas assez d'effecteurs light au sol capables d'arriver à temps et en énergie (estimation en ligne directe, routage réel non disponible) [routage réel : budget de test dépassé]
- **C40** · hostile, 57 pts, besoin : 3 light, 1 heavy, fenêtre 194–378 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C19** · hostile, 51 pts, besoin : 2 light, 2 heavy, fenêtre 156–345 s · interdit par R7 (à 161 m de C74, friendly)
- **C31** · hostile, 49 pts, besoin : 2 heavy, fenêtre 386–694 s · interdit par R7 (à 186 m de C74, friendly)
- **C48** · hostile, 49 pts, besoin : 2 light, fenêtre 43–317 s · routable seul, mais les drones nécessaires sont déjà pris par un autre contact dans notre plan (concurrence de ressources)
- **C28** · hostile, 47 pts, besoin : 3 light, fenêtre 90–389 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C03** · hostile, 44 pts, besoin : 1 light, 1 heavy, fenêtre 246–593 s · interdit par R7 (à 190 m de C76, friendly)
- **C01** · hostile, 43 pts, besoin : 3 light, 1 heavy, fenêtre 44–365 s · interdit par R7 (à 154 m de C74, friendly)
- **C36** · hostile, 42 pts, besoin : 2 light, 1 heavy, fenêtre 316–549 s · pas assez d'effecteurs light au sol capables d'arriver à temps et en énergie (estimation en ligne directe, routage réel non disponible) [routage réel : budget de test dépassé]
- **C55** · unknown, 23 pts, besoin : observation, fenêtre 0–324 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C58** · unknown, 21 pts, besoin : observation, fenêtre 419–678 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C59** · unknown, 18 pts, besoin : observation, fenêtre 34–306 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C65** · unknown, 18 pts, besoin : observation, fenêtre 418–734 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C60** · unknown, 16 pts, besoin : observation, fenêtre 113–297 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C66** · unknown, 15 pts, besoin : observation, fenêtre 72–290 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C64** · unknown, 13 pts, besoin : observation, fenêtre 444–710 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **39 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **208 pts** (gagnable seulement en sacrifiant un autre contact).
